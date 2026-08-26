from py4web import URL, request, response, redirect, action
from datetime import timedelta
from ..utils.common import session, flash, view_page
from ..core.db import db, db_datetime
from ..core.config import settings

@action("auth/login", method=["GET", "POST"])
@view_page("auth/login.html", title="Login | EMS Admin")
def login():
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    error = None
    if session.userorized or session.user:
        redirect(URL("dashboard"))
    
    if request.method == "POST":
        username = request.forms.get("username")
        password = request.forms.get("password")

        user_auth_sql = """
        SELECT
            u.id,
            COALESCE(u.cid, '') AS cid,
            u.user_id,
            u.user_pass,
            u.user_name,
            u.role_id AS user_role,
            u.email AS user_email,
            u.mobile AS user_mobile,
            COALESCE(u.profile_image, '') AS profile_image,
            u.sync_code,
            u.sync_count,
            u.fcm_token,
            u.device_id,
            u.failed_login_attempts,
            u.account_locked_until,
            u.status_type AS account_status,
            UPPER(COALESCE(r.status_type, '')) AS role_status
        FROM 
            users u
        LEFT JOIN
            roles r ON u.role_id = r.role_id
        WHERE
            u.user_id = %s
        LIMIT 1;
        """
        user_record = db.executesql(user_auth_sql, placeholders=[username], as_dict=True)
        
        if not user_record:
            error = "Invalid User ID or Password. Please try again."
        else:
            user = user_record[0]
            row_id = user.get("id")
            cid = user.get("cid", '')
            user_pass = user.get("user_pass")
            user_email = user.get("user_email")
            user_mobile = user.get("user_mobile")
            account_status = (user.get("account_status") or "").upper()
            role_status = user.get("role_status", "")

            if account_status != "ACTIVE":
                error = f"Your account is {account_status}. Please contact the administrator."
            elif role_status != "ACTIVE":
                error = "Your assigned role is inactive or invalid. Please contact the administrator."
            elif cid:
                company_record_sql = "SELECT legal_name FROM companies WHERE cid = %s AND status_type = 'ACTIVE' LIMIT 1"
                company_record = db.executesql(company_record_sql, placeholders=[cid], as_dict=True)
                if not company_record:
                    error = "Company account is inactive or invalid. Please contact the administrator."
                else:
                    user['company_name'] = company_record[0].get("legal_name", "")

            # 4. Lockout & Password authentication check
            if not error:
                failed_attempts = user.get("failed_login_attempts") or 0
                account_locked_until = user.get("account_locked_until")

                if account_locked_until and account_locked_until > db_datetime:
                    remaining_time = int((account_locked_until - db_datetime).total_seconds() / 60)
                    error = f"Too many failed login attempts. Account is locked. Try again after {remaining_time + 1} minute(s)."
                elif user_pass != password:
                    new_failed_attempts = failed_attempts + 1
                    max_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS
                    lock_duration = settings.ACCOUNT_LOCKOUT_MINUTES

                    if new_failed_attempts >= max_attempts:
                        lock_until = db_datetime + timedelta(minutes=lock_duration)
                        update_lock_sql = """
                        UPDATE users 
                        SET failed_login_attempts = %s, account_locked_until = %s 
                        WHERE id = %s
                        """
                        db.executesql(update_lock_sql, placeholders=[new_failed_attempts, lock_until, row_id])
                        db.commit()

                        error = f"Too many failed attempts. Your account has been locked for {lock_duration} minutes."
                    else:
                        update_failed_sql = """
                        UPDATE users 
                        SET failed_login_attempts = %s 
                        WHERE id = %s
                        """
                        db.executesql(update_failed_sql, placeholders=[new_failed_attempts, row_id])
                        db.commit()
                        error = "Invalid User ID or Password."
                else:
                    # Successful login
                    update_success_sql = """
                    UPDATE users 
                    SET failed_login_attempts = 0, 
                        account_locked_until = NULL, 
                        last_login_on = %s
                    WHERE id = %s
                    """
                    db.executesql(update_success_sql, placeholders=[db_datetime, row_id])
                    db.commit()

                    user.pop("user_pass", None)
                    session.user = user
                    session.userorized = True
                    
                    try:
                        from ..utils.menu_utils import get_user_menu_tree
                        session.user_menu = get_user_menu_tree(user)
                    except Exception:
                        session.user_menu = []
                        
                    redirect(URL("dashboard"))

    return dict(error=error)

@action("auth/logout")
@action.uses(session)
def logout():
    session.clear()
    session.user_menu = None
    try:
        response.delete_cookie(f"{settings.APP_NAME}_session")
    except Exception:
        pass
    redirect(URL("auth/login"))
