from py4web import DAL
from datetime import datetime, timedelta

db = DAL("mysql://root@localhost/badc", pool_size=10, migrate_enabled=False)

db_datetime = datetime.now() + timedelta(hours=6)