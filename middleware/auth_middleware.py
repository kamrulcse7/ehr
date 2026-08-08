from functools import wraps
from datetime import datetime, timedelta
from py4web import request, response, redirect, URL
from ..utils.common import session, flash
from ..core.config import settings

def web_auth_required(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        is_authenticated = True
        
        if not session.userorized or not session.user:
            is_authenticated = False
            
        last_activity_str = session.get("last_activity")

        if last_activity_str and is_authenticated:
            try:
                last_activity = datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S")
                expiry_minutes = settings.WEB_SESSION_EXPIRE_MINUTES
                
                if datetime.now() - last_activity > timedelta(minutes=expiry_minutes):
                    is_authenticated = False
            except Exception:
                is_authenticated = False

        if not is_authenticated:
            session.clear()
            response.delete_cookie("3DB-AUTH-1")
            redirect(URL("auth/login"))
            return

        session.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        response_dict = handler(*args, **kwargs)

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        if isinstance(response_dict, dict):
            if "session" not in response_dict:
                response_dict["session"] = session
            if "flash" not in response_dict:
                response_dict["flash"] = flash
                
        return response_dict

    return wrapper