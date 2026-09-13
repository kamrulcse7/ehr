from py4web import URL, action, redirect, request, response
from datetime import datetime
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import flash, session, view_page
from ..utils.permission_utils import get_user_permissions
from ..core.db import db, db_datetime


@action("dashboard/index")
@view_page("dashboard/index.html", title="Dashboard | EMS")
@web_auth_required
def dashboard():
    user = session.get("user") or {}
    user_role = (user.get("user_role") or "").upper()
    cid = user.get("cid") or ""
    is_system_user = user_role in ("SUPER_ADMIN", "SYSTEM_ADMIN", "ROOT") or not cid

    # Metrics container
    metrics = {
        "total_companies": 0,
        "total_users": 0,
        "total_employees": 0,
        "total_roles": 0,
        "pending_transfers": 0,
        "total_branches": 0,
        "total_departments": 0,
    }

    recent_companies = []
    recent_users = []
    recent_employees = []
    recent_transfers = []

    if is_system_user:
        # 1. System Admin Core Metric 1: Total Companies
        try:
            res_comp = db.executesql("SELECT COUNT(*) AS cnt FROM companies WHERE status_type = 'ACTIVE';", as_dict=True)
            metrics["total_companies"] = res_comp[0]["cnt"] if res_comp else 0
        except Exception:
            metrics["total_companies"] = 0

        # 2. System Admin Core Metric 2: Total Users
        try:
            res_usr = db.executesql("SELECT COUNT(*) AS cnt FROM users WHERE status_type = 'ACTIVE';", as_dict=True)
            metrics["total_users"] = res_usr[0]["cnt"] if res_usr else 0
        except Exception:
            metrics["total_users"] = 0

        # 3. System Admin Core Metric 3: Total Employees
        try:
            res_emp_all = db.executesql("SELECT COUNT(*) AS cnt FROM employees WHERE status_type = 'ACTIVE';", as_dict=True)
            metrics["total_employees"] = res_emp_all[0]["cnt"] if res_emp_all else 0
        except Exception:
            metrics["total_employees"] = 0

        # 4. System Admin Core Metric 4: Total Roles
        try:
            res_roles = db.executesql("SELECT COUNT(*) AS cnt FROM roles WHERE status_type = 'ACTIVE';", as_dict=True)
            metrics["total_roles"] = res_roles[0]["cnt"] if res_roles else 0
        except Exception:
            metrics["total_roles"] = 0

        # System Admin Feeds: Recent Companies, Recent Users, Recent Employees
        try:
            recent_companies = db.executesql(
                "SELECT cid, company_name, legal_name, business_type, created_on, status_type FROM companies ORDER BY id DESC LIMIT 6;",
                as_dict=True
            )
        except Exception:
            recent_companies = []

        try:
            recent_users = db.executesql(
                """
                SELECT u.id, u.user_id, u.user_name, u.role_id, u.cid, u.status_type, u.created_on,
                       COALESCE(c.company_name, u.cid, 'System Global') AS company_display
                FROM users u
                LEFT JOIN companies c ON LOWER(u.cid) = LOWER(c.cid)
                ORDER BY u.id DESC LIMIT 6;
                """,
                as_dict=True
            )
        except Exception:
            recent_users = []

        try:
            recent_employees_sql = """
            SELECT 
                e.emp_id, 
                e.emp_name, 
                e.emp_designation, 
                e.cid,
                COALESCE(c.company_name, e.cid, 'Head Office') AS company_display,
                e.join_date 
            FROM employees e
            LEFT JOIN companies c ON LOWER(e.cid) = LOWER(c.cid)
            WHERE e.status_type = 'ACTIVE' 
            ORDER BY e.id DESC LIMIT 6;
            """
            recent_employees = db.executesql(recent_employees_sql, as_dict=True)
        except Exception:
            recent_employees = []

    else:
        # Company User Metrics (scoped to user's cid)
        try:
            res_emp = db.executesql("SELECT COUNT(*) AS cnt FROM employees WHERE LOWER(cid) = LOWER(%s) AND status_type = 'ACTIVE';", placeholders=[cid], as_dict=True)
            metrics["total_employees"] = res_emp[0]["cnt"] if res_emp else 0
        except Exception:
            metrics["total_employees"] = 0

        try:
            res_tr = db.executesql("SELECT COUNT(*) AS cnt FROM employee_transfers WHERE LOWER(cid) = LOWER(%s) AND (joining_status = 'PENDING' OR status_type IN ('SUBMITTED', 'PROCESSING', 'PENDING'));", placeholders=[cid], as_dict=True)
            metrics["pending_transfers"] = res_tr[0]["cnt"] if res_tr else 0
        except Exception:
            metrics["pending_transfers"] = 0

        try:
            res_br = db.executesql("SELECT COUNT(*) AS cnt FROM branches WHERE LOWER(cid) = LOWER(%s) AND status_type = 'ACTIVE';", placeholders=[cid], as_dict=True)
            metrics["total_branches"] = res_br[0]["cnt"] if res_br else 0
        except Exception:
            metrics["total_branches"] = 0

        try:
            res_dept = db.executesql("SELECT COUNT(*) AS cnt FROM departments WHERE LOWER(cid) = LOWER(%s) AND status_type = 'ACTIVE';", placeholders=[cid], as_dict=True)
            metrics["total_departments"] = res_dept[0]["cnt"] if res_dept else 0
        except Exception:
            metrics["total_departments"] = 0

        try:
            recent_employee_records_sql = """
            SELECT 
                e.emp_id, 
                e.emp_name, 
                e.emp_designation, 
                e.current_branch_id,
                COALESCE(b.branch_name, e.current_branch_id, 'Head Office') AS current_posting_place,
                e.join_date 
            FROM employees e
            LEFT JOIN branches b ON e.current_branch_id = b.branch_id AND LOWER(e.cid) = LOWER(b.cid)
            WHERE LOWER(e.cid) = LOWER(%s) AND e.status_type = 'ACTIVE' 
            ORDER BY e.id DESC LIMIT 6;
            """
            recent_employees = db.executesql(recent_employee_records_sql, placeholders=[cid], as_dict=True)
        except Exception:
            recent_employees = []

        try:
            recent_transfers_sql = """
            SELECT 
                t.id,
                COALESCE(t.transfer_order_no, CONCAT('TR-', t.id)) AS transfer_order_no,
                t.emp_id,
                e.emp_name,
                COALESCE(t.to_designation, e.emp_designation) AS designation,
                t.from_branch_id,
                t.to_branch_id,
                COALESCE(fb.branch_name, t.from_branch_id, 'N/A') AS from_posting_place,
                COALESCE(tb.branch_name, t.to_branch_id, 'N/A') AS to_posting_place,
                t.order_date,
                t.joining_status,
                t.status_type
            FROM employee_transfers t
            LEFT JOIN employees e ON t.emp_id = e.emp_id AND LOWER(t.cid) = LOWER(e.cid)
            LEFT JOIN branches fb ON t.from_branch_id = fb.branch_id AND LOWER(t.cid) = LOWER(fb.cid)
            LEFT JOIN branches tb ON t.to_branch_id = tb.branch_id AND LOWER(t.cid) = LOWER(tb.cid)
            WHERE LOWER(t.cid) = LOWER(%s)
            ORDER BY t.id DESC 
            LIMIT 6;
            """
            recent_transfers = db.executesql(recent_transfers_sql, placeholders=[cid], as_dict=True)
        except Exception:
            recent_transfers = []

    for emp in recent_employees:
        raw_d = emp.get('join_date')
        if not raw_d:
            emp['join_date'] = 'N/A'
            continue
            
        d_obj = datetime.strptime(str(raw_d), '%Y-%m-%d').date() if isinstance(raw_d, str) else raw_d
        diff = (db_datetime.date() - d_obj).days

        if diff == 0:
            emp['join_date'] = 'Today'
        elif diff == 1:
            emp['join_date'] = 'Yesterday'
        elif 2 <= diff <= 30:
            emp['join_date'] = f"{diff} days ago"
        else:
            emp['join_date'] = d_obj.strftime('%Y-%m-%d')

    for tr in recent_transfers:
        raw_order_date = tr.get('order_date')
        if raw_order_date:
            d_obj = datetime.strptime(str(raw_order_date), '%Y-%m-%d').date() if isinstance(raw_order_date, str) else raw_order_date
            tr['formatted_order_date'] = d_obj.strftime('%d %b, %Y')
        else:
            tr['formatted_order_date'] = 'N/A'

    # Check key module permissions for dynamic card visibility (supporting both standard & alias module_ids)
    mod_perms = {
        "can_view_employees": get_user_permissions(user, "EMPLOYEE_DIR").get("can_view", False) or get_user_permissions(user, "EMP_DIRECTORY").get("can_view", False),
        "can_view_transfers": get_user_permissions(user, "POSTING_TRANS").get("can_view", False) or get_user_permissions(user, "EMP_TRANSFERS").get("can_view", False),
        "can_view_branches": get_user_permissions(user, "ORG_BRANCHES").get("can_view", False) or get_user_permissions(user, "BRANCH").get("can_view", False) or True,
        "can_view_departments": get_user_permissions(user, "ORG_DEPARTMENTS").get("can_view", False) or get_user_permissions(user, "DEPARTMENT").get("can_view", False) or True,
        "can_view_reports": get_user_permissions(user, "EMP_REPORTS").get("can_view", False) or get_user_permissions(user, "REPORTS").get("can_view", False),
        "can_view_settings": get_user_permissions(user, "SETTINGS").get("can_view", False),
        "can_view_users": get_user_permissions(user, "USER_MGMT").get("can_view", False),
        "can_view_roles": get_user_permissions(user, "ROLES_PERM").get("can_view", False),
        "can_view_companies": get_user_permissions(user, "COMPANY_MGMT").get("can_view", False),
        "can_view_audit_logs": get_user_permissions(user, "AUDIT_LOGS").get("can_view", False),
    }

    return dict(
        is_system_user=is_system_user,
        user_role=user_role,
        user_name=user.get("user_name") or user.get("user_id") or "",
        company_name=user.get("company_name", ""),
        metrics=metrics,
        recent_companies=recent_companies,
        recent_users=recent_users,
        recent_employees=recent_employees,
        recent_transfers=recent_transfers,
        mod_perms=mod_perms
    )