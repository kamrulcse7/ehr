from py4web import URL, request, redirect, action
from ..utils.common import session, flash, db, view_page
from ..middleware.auth_middleware import web_auth_required

@action("auth/login", method=["GET", "POST"])
@view_page("auth/login.html")
def login():
    error = None
    page_title = "Login | HRMS Admin"
    if session.authorized or session.auth:
        redirect(URL("dashboard"))
    
    if request.method == "POST":
        username = request.forms.get("username")
        password = request.forms.get("password")

        user_auth_sql = """
        SELECT
            u.user_id,
            u.user_pass,
            u.user_type,
            u.user_name,
            u.email AS user_email,
            u.mobile AS user_mobile,
            r.role_id,
            f.two_fa_method,
            f.two_fa_secret,
            u.status_type AS account_status,
            r.status_type AS role_status,
            f.status_type AS tow_fa_status,
            u.cid,
            c.company_name,
            c.legal_name,
            c.email AS company_email,
            c.phone AS company_phone,
            c.website,
            c.address_line1,
            c.address_line2,
            c.city,
            c.state,
            c.country,
            c.postal_code,
            c.timezone,
            c.fiscal_year_start_month,
            c.favicon_url,
            c.logo_url,
            c.banner_url,
            c.status_type AS company_status
        FROM 
            users u
        LEFT JOIN
            user_roles r ON u.user_id = r.user_id
        LEFT JOIN
            users_2fa_config f ON u.user_id = f.user_id
        LEFT JOIN
            companies c ON u.cid = c.cid
        WHERE
            u.user_id = %s
        LIMIT 1;
        """
        user_record = db.executesql(user_auth_sql, placeholders=[username], as_dict=True)
        
        if not user_record:
            error = "Invalid User ID or Password. Please try again."
        else:
            user = user_record[0]
            user_pass = user.get("user_pass")
            user_email = user.get("user_email")
            user_mobile = user.get("user_mobile")
            account_status = user.get("account_status")
            role_status = user.get("role_status")
            cid = user.get("cid")
            company_status = user.get("company_status")
            two_fa_status = user.get("two_fa_status")
            two_fa_method = str(user.get("two_fa_method", '')).upper()
            user.pop("user_pass", None)
            session.user_id = user_email
            if user_pass != password:
                error = "Invalid User ID or Password. Please try again."
            elif account_status != "ACTIVE":
                error = f"Your account is {account_status}. Please contact the administrator."
            elif cid and company_status != "ACTIVE":
                error = f"Your company is {company_status}. Please contact the administrator."
            elif role_status != "ACTIVE":
                error = f"Role not assigned yet. Please contact the administrator."
            elif two_fa_status == "ACTIVE":
                if (two_fa_method == 'EMAIL' and not user_email) or (two_fa_method == 'MOBILE' and not user_mobile):
                    error = f"2FA is enabled via {two_fa_method}, but no valid contact info found. Contact admin."
                else:
                    session.temp_2fa_info = user
                    redirect(URL("two_fa_verification"))
            else:
                if not cid:
                    user['company_name'] = 'Eon Systems'
                    
                session.auth = user
                session.authorized = True
                redirect(URL("dashboard"))    

            
    return dict(
        error=error, 
        page_title=page_title
    )


@action("auth/logout")
@action.uses(session)
def logout():
    session.clear()
    redirect(URL("auth/login"))


