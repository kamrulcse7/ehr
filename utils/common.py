from py4web import Session, Flash, action, DAL
from ..core.config import settings

session = Session(
    name=settings.APP_NAME,
    same_site=settings.SAME_SITE,
    secret=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM,
    expiration=settings.WEB_SESSION_EXPIRE_MINUTES,
)
flash = Flash()


db = DAL("mysql://root@localhost/aibl", pool_size=10, migrate_enabled=False)

view_page = lambda template: action.uses(template, session, flash, db)

