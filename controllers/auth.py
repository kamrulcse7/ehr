from py4web import URL, request, redirect, action
from datetime import timedelta
from ..utils.common import session, flash, view_page
from ..core.db import db, db_datetime
from ..core.config import settings

@action("auth/login", method=["GET", "POST"])
@view_page("auth/login.html", title="Login | EMS Admin")
def login():
    error = None
    if session.userorized or session.user:
        redirect(URL("dashboard"))
    
    if request.method == "POST":
        username = request.forms.get("username")
        password = request.forms.get("password")

        user_auth_sql = """
        SELECT
            id,
            user_id,
            user_pass,
            user_name,
            user_role,
            email AS user_email,
            mobile AS user_mobile,
            COALESCE(profile_image, '') AS profile_image,
            sync_code,
            sync_count,
            fcm_token,
            device_id,
            failed_login_attempts,
            account_locked_until,
            status_type AS account_status
        FROM 
            users
        WHERE
            user_id = %s
        LIMIT 1;
        """
        user_record = db.executesql(user_auth_sql, placeholders=[username], as_dict=True)
        
        if not user_record:
            error = "Invalid User ID or Password. Please try again."
        else:
            user = user_record[0]
            row_id = user.get("id")
            user_pass = user.get("user_pass")
            user_email = user.get("user_email")
            user_mobile = user.get("user_mobile")
            account_status = user.get("account_status")
            user_role = user.get("user_role", "")
           

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
                    error = f"Invalid User ID or Password"
            elif account_status != "ACTIVE":
                error = f"Your account is {account_status}. Please contact the administrator."
            else:
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
                # return "daat"
                session.user = user
                session.userorized = True
                # return session.user
                redirect(URL("dashboard"))         

    return dict(error=error)

@action("auth/logout")
@action.uses(session)
def logout():
    session.clear()
    redirect(URL("auth/login"))


