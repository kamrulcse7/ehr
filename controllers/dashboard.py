from py4web import URL, action, redirect, request, response
from datetime import datetime
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import flash, session, view_page
from ..core.db import db, db_datetime


@action("dashboard/index")
@view_page("dashboard/index.html", title="Dashboard | EMS")
@web_auth_required
def dashboard():
    # flash.set("Welcome to HRMS", "success")
    recent_employee_records_sql = """
    SELECT 
        e.emp_id, 
        e.emp_name, 
        e.emp_designation, 
        e.current_branch_id,
        COALESCE(b.branch_name, e.current_branch_id, 'Head Office') AS current_posting_place,
        e.join_date 
    FROM employees e
    LEFT JOIN branches b ON e.current_branch_id = b.branch_id AND e.cid = b.cid
    WHERE e.status_type = 'ACTIVE' 
    ORDER BY e.id DESC LIMIT 10;
    """
    recent_employees = db.executesql(recent_employee_records_sql, as_dict=True)
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

    recent_transfers_sql = """
    SELECT 
        t.id,
        t.transfer_order_no,
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
    LEFT JOIN employees e ON t.emp_id = e.emp_id AND t.cid = e.cid
    LEFT JOIN branches fb ON t.from_branch_id = fb.branch_id AND t.cid = fb.cid
    LEFT JOIN branches tb ON t.to_branch_id = tb.branch_id AND t.cid = tb.cid
    ORDER BY t.id DESC 
    LIMIT 10;
    """
    recent_transfers = db.executesql(recent_transfers_sql, as_dict=True)

    # Date format formatting (e.g., 24 Oct, 2026)
    for tr in recent_transfers:
        raw_order_date = tr.get('order_date')
        if raw_order_date:
            d_obj = datetime.strptime(str(raw_order_date), '%Y-%m-%d').date() if isinstance(raw_order_date, str) else raw_order_date
            tr['formatted_order_date'] = d_obj.strftime('%d %b, %Y')
        else:
            tr['formatted_order_date'] = 'N/A'

    return dict(
        recent_employees=recent_employees,
        recent_transfers=recent_transfers,
    )