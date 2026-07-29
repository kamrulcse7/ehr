from py4web import URL, action, redirect, request, response
from datetime import datetime
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import flash, session, view_page
from ..core.db import db, db_datetime


@action("dashboard/index")
@view_page("dashboard/index.html", title="Dashboard | EMS")
@web_auth_required
def dashboard():
    recent_employee_records_sql = """
    SELECT emp_id, emp_name, card_number, emp_type, emp_department, 
            emp_designation, emp_grade, current_posting_place, 
            current_posting_join_date, current_grade_join_date, mobile, 
            email, gender, dob, blood_group, join_date, retirement_date, 
            edu_qualification, home_district, present_address, permanent_address, 
            nid_number, photo_url, note 
    FROM employees 
    WHERE status_type = 'ACTIVE' 
    ORDER BY id DESC LIMIT 10;
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
        t.from_posting_place,
        t.to_posting_place,
        t.order_date,
        t.joining_status,
        t.status_type
    FROM employee_transfers t
    LEFT JOIN employees e ON t.emp_id = e.emp_id
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