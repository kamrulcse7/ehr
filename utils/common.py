from functools import wraps
from py4web import Session, Flash, action
from ..core.config import settings
from ..core.db import db

session = Session(
    name=f"{settings.APP_NAME}_session",
    same_site=settings.SAME_SITE,
    secret=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM,
    expiration=settings.WEB_SESSION_EXPIRE_MINUTES * 60,
)

flash = Flash()

def view_page(template, title=None):
    def decorator(func):
        @action.uses(template, session, flash, db)
        @wraps(func)
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if isinstance(res, dict) and title:
                res.setdefault("page_title", title)
            return res
        return wrapper
    return decorator