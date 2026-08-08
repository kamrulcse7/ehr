
from py4web import DAL
from datetime import datetime, timedelta
from ..core.config import settings

db = DAL("mysql://root@localhost/badc", pool_size=10, migrate_enabled=False)

# db = DAL(f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASS}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB_NAME}", pool_size=10, migrate_enabled=False)

db_datetime = datetime.now() + timedelta(hours=settings.TIMEZONE_OFFSET_HOURS, minutes=settings.TIMEZONE_OFFSET_MINUTES, seconds=settings.TIMEZONE_OFFSET_SECONDS)