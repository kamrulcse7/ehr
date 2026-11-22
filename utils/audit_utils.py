import json
from py4web import request
from ..utils.common import db, session
from ..core.db import db_datetime


def log_audit(action, module, table_name=None, record_id=None, old_values=None, new_values=None, user_info=None):
    try:
        user = user_info or (session.user if hasattr(session, "user") else None) or {}
        cid = user.get("cid") or ""
        user_id = user.get("user_id") or ""
        user_name = user.get("user_name") or user_id or ""

        # Extract client IP
        ip = getattr(request, "remote_addr", "") or ""
        if hasattr(request, "headers") and request.headers:
            forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()

        # Extract user agent
        user_agent = ""
        if hasattr(request, "headers") and request.headers:
            user_agent = (request.headers.get("user-agent") or request.headers.get("User-Agent") or "")[:255]

        old_val_str = json.dumps(old_values, default=str) if old_values is not None and not isinstance(old_values, str) else old_values
        new_val_str = json.dumps(new_values, default=str) if new_values is not None and not isinstance(new_values, str) else new_values

        sql = """
            INSERT INTO audit_logs 
            (cid, user_id, user_name, action, module, table_name, record_id, old_values, new_values, ip_address, user_agent, created_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            cid, user_id, user_name,
            str(action).upper(), str(module).upper(),
            table_name, str(record_id) if record_id is not None else None,
            old_val_str, new_val_str,
            ip, user_agent, db_datetime
        ]
        db.executesql(sql, params)
        db.commit()
    except Exception as e:
        print(f"[AuditLog Error]: {e}")
