from py4web import URL, action, redirect, request, response
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import flash, session, view_page
from ..core.db import db, db_datetime
import xml.sax.saxutils as xml_escape
import math
import io
import csv
import os
import time

@action("employees/personnel_directory")
@view_page("employees/personnel_directory.html", title="Personnel Directory | EMS")
@web_auth_required
def personnel_directory():
    keywords = request.query.get("keywords", "").strip()
    department = request.query.get("department", "").strip()
    status = request.query.get("status", "").strip()
    export_format = request.query.get("export", "").strip().lower()

    # 1. Build SQL WHERE conditions
    where_clauses = ["1=1"]
    params = []

    if keywords:
        where_clauses.append("(emp_id LIKE %s OR emp_name LIKE %s OR mobile LIKE %s)")
        search_term = f"%{keywords}%"
        params.extend([search_term, search_term, search_term])

    if department:
        where_clauses.append("emp_department = %s")
        params.append(department)

    if status:
        where_clauses.append("status_type = %s")
        params.append(status)

    where_str = " AND ".join(where_clauses)

    if export_format in ["xlsx", "xls", "csv"]:
        export_sql = f"""
            SELECT id, emp_id, emp_name, card_number, emp_type, emp_department, emp_designation, emp_grade, 
                   current_posting_place, current_posting_join_date, current_grade_join_date, mobile, email, 
                   gender, dob, blood_group, join_date, confirmation_date, retirement_date, edu_qualification, 
                   home_district, present_address, permanent_address, nid_number, photo_url, note, status_type
            FROM employees 
            WHERE {where_str} 
            ORDER BY id DESC
        """
        export_records = db.executesql(export_sql, params, as_dict=True)
        filename = f"Employee_List_Full_{db_datetime.strftime('%Y%m%d_%H%M%S')}"

        headers = [
            "ID", "Employee ID", "Full Name", "Card Number", "Employment Type", "Department", "Designation", "Grade",
            "Posting Place", "Posting Join Date", "Grade Join Date", "Mobile", "Email", "Gender", "DOB",
            "Blood Group", "Join Date", "Confirmation Date", "Retirement Date", "Education", "Home District",
            "Present Address", "Permanent Address", "NID Number", "Photo URL", "Note", "Status"
        ]

        # CSV EXPORT
        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for emp in export_records:
                writer.writerow([
                    emp.get('id', ''), emp.get('emp_id', ''), emp.get('emp_name', ''), emp.get('card_number', ''),
                    emp.get('emp_type', ''), emp.get('emp_department', ''), emp.get('emp_designation', ''), emp.get('emp_grade', ''),
                    emp.get('current_posting_place', ''), emp.get('current_posting_join_date', ''), emp.get('current_grade_join_date', ''),
                    emp.get('mobile', ''), emp.get('email', ''), emp.get('gender', ''), emp.get('dob', ''),
                    emp.get('blood_group', ''), emp.get('join_date', ''), emp.get('confirmation_date', ''), emp.get('retirement_date', ''),
                    emp.get('edu_qualification', ''), emp.get('home_district', ''), emp.get('present_address', ''), emp.get('permanent_address', ''),
                    emp.get('nid_number', ''), emp.get('photo_url', ''), emp.get('note', ''), emp.get('status_type', '')
                ])
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return output.getvalue()

        # EXCEL (.XLS) EXPORT 
        if export_format in ["xlsx", "xls"]:
            xml_data = []
            xml_data.append('<?xml version="1.0" encoding="UTF-8"?>')
            xml_data.append('<?mso-application progid="Excel.Sheet"?>')
            xml_data.append('<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">')
            xml_data.append('<Styles>')
            xml_data.append(' <Style ss:ID="HeaderStyle"><Font ss:FontName="Calibri" ss:Size="11" ss:Color="#FFFFFF" ss:Bold="1"/><Interior ss:Color="#0F172A" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/></Style>')
            xml_data.append(' <Style ss:ID="DataLeft"><Font ss:FontName="Calibri" ss:Size="10"/><Alignment ss:Horizontal="Left" ss:Vertical="Center"/></Style>')
            xml_data.append(' <Style ss:ID="DataCenter"><Font ss:FontName="Calibri" ss:Size="10"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/></Style>')
            xml_data.append('</Styles>')
            xml_data.append('<Worksheet ss:Name="Full Employee Records"><Table>')

            xml_data.append('<Row ss:Height="26">')
            for h in headers:
                xml_data.append(f'<Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{xml_escape.escape(h)}</Data></Cell>')
            xml_data.append('</Row>')

            for emp in export_records:
                xml_data.append('<Row ss:Height="22">')
                row_fields = [
                    (emp.get('id') or '', 'DataCenter'), (emp.get('emp_id') or '', 'DataCenter'),
                    (emp.get('emp_name') or '', 'DataLeft'), (emp.get('card_number') or '', 'DataCenter'),
                    (emp.get('emp_type') or '', 'DataCenter'), (emp.get('emp_department') or '', 'DataLeft'),
                    (emp.get('emp_designation') or '', 'DataLeft'), (emp.get('emp_grade') or '', 'DataCenter'),
                    (emp.get('current_posting_place') or '', 'DataLeft'), (emp.get('current_posting_join_date') or '', 'DataCenter'),
                    (emp.get('current_grade_join_date') or '', 'DataCenter'), (emp.get('mobile') or '', 'DataCenter'),
                    (emp.get('email') or '', 'DataLeft'), (emp.get('gender') or '', 'DataCenter'),
                    (emp.get('dob') or '', 'DataCenter'), (emp.get('blood_group') or '', 'DataCenter'),
                    (emp.get('join_date') or '', 'DataCenter'), (emp.get('confirmation_date') or '', 'DataCenter'),
                    (emp.get('retirement_date') or '', 'DataCenter'), (emp.get('edu_qualification') or '', 'DataLeft'),
                    (emp.get('home_district') or '', 'DataLeft'), (emp.get('present_address') or '', 'DataLeft'),
                    (emp.get('permanent_address') or '', 'DataLeft'), (emp.get('nid_number') or '', 'DataCenter'),
                    (emp.get('photo_url') or '', 'DataLeft'), (emp.get('note') or '', 'DataLeft'),
                    (emp.get('status_type') or '', 'DataCenter')
                ]
                for val, style in row_fields:
                    xml_data.append(f'<Cell ss:StyleID="{style}"><Data ss:Type="String">{xml_escape.escape(str(val))}</Data></Cell>')
                xml_data.append('</Row>')

            xml_data.append('</Table></Worksheet></Workbook>')
            response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
            return "\n".join(xml_data)
        
    allowed_limits = [10, 25, 50, 100]
    try:
        limit = int(request.query.get("limit", 10))
        if limit not in allowed_limits: limit = 10
    except ValueError: limit = 10

    try: page = max(1, int(request.query.get("page", 1)))
    except ValueError: page = 1
        
    offset = (page - 1) * limit

    count_sql = f"SELECT COUNT(id) as total FROM employees WHERE {where_str}"
    total_items = db.executesql(count_sql, params, as_dict=True)[0]['total']

    records_sql = f"""
        SELECT id, emp_id, emp_name, emp_designation, emp_grade, emp_department, 
               current_posting_place, mobile, home_district, status_type, blood_group 
        FROM employees WHERE {where_str} ORDER BY id DESC LIMIT %s OFFSET %s
    """
    employees_list = db.executesql(records_sql, params + [limit, offset], as_dict=True)

    stats_sql = """
        SELECT COUNT(id) as total,
            COUNT(CASE WHEN status_type = 'ACTIVE' THEN 1 END) as active,
            COUNT(CASE WHEN status_type = 'PROBATIONARY' THEN 1 END) as probationary,
            COUNT(CASE WHEN status_type = 'INACTIVE' THEN 1 END) as inactive
        FROM employees
    """
    stats_res = db.executesql(stats_sql, as_dict=True)[0]

    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    start_item = offset + 1 if total_items > 0 else 0
    end_item = min(offset + limit, total_items)

    pagination = {
        "current_page": page, "total_pages": total_pages,
        "total_items": total_items, "start_item": start_item,
        "end_item": end_item, "limit": limit
    }

    return dict(employees=employees_list, pagination=pagination, stats=stats_res)



@action("employees/add_directory", method=["GET", "POST"])
@view_page("employees/add_directory.html", title="Add Directory | EMS")
@web_auth_required
def add_directory():
    msg = None
    msg_type = None

    if request.method == "POST":
        try:
            def clean_val(val):
                val = str(val).strip() if val else None
                return val if val != "" else None

            emp_name = clean_val(request.forms.get("emp_name"))
            mobile = clean_val(request.forms.get("mobile"))
            email = clean_val(request.forms.get("email"))
            nid_number = clean_val(request.forms.get("nid_number"))
            dob = clean_val(request.forms.get("dob"))
            gender = clean_val(request.forms.get("gender"))
            blood_group = clean_val(request.forms.get("blood_group"))
            edu_qualification = clean_val(request.forms.get("edu_qualification"))

            emp_id = clean_val(request.forms.get("emp_id"))
            card_number = clean_val(request.forms.get("card_number"))
            emp_type = clean_val(request.forms.get("emp_type"))
            emp_department = clean_val(request.forms.get("emp_department"))
            emp_designation = clean_val(request.forms.get("emp_designation"))
            emp_grade = clean_val(request.forms.get("emp_grade"))
            join_date = clean_val(request.forms.get("join_date"))
            confirmation_date = clean_val(request.forms.get("confirmation_date"))
            current_grade_join_date = clean_val(request.forms.get("current_grade_join_date"))
            
            current_posting_place = clean_val(request.forms.get("current_posting_place"))
            current_posting_join_date = clean_val(request.forms.get("current_posting_join_date"))
            retirement_date = clean_val(request.forms.get("retirement_date"))

            home_district = clean_val(request.forms.get("home_district"))
            present_address = clean_val(request.forms.get("present_address"))
            permanent_address = clean_val(request.forms.get("permanent_address"))
            note = clean_val(request.forms.get("note"))
            
            photo = request.files.get("emp_photo")
            saved_filename = None

            if photo and photo.filename:
                UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "profile_images")
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                ext = os.path.splitext(photo.filename)[1]
                saved_filename = f"{emp_id}_{int(time.time())}{ext}"
                file_path = os.path.join(UPLOAD_DIR, saved_filename)
                with open(file_path, "wb") as f:
                    f.write(photo.file.read())

            insert_sql = """
            INSERT INTO employees (
                emp_id, emp_name, card_number, emp_type, emp_department, 
                emp_designation, emp_grade, current_posting_place, current_posting_join_date, 
                current_grade_join_date, mobile, email, gender, dob, 
                blood_group, join_date, confirmation_date, retirement_date, 
                edu_qualification, home_district, present_address, permanent_address, 
                nid_number, photo_url, note, status_type, created_on, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s
                )
            """
            values = (
                emp_id, emp_name, card_number, emp_type, emp_department,
                emp_designation, emp_grade, current_posting_place, current_posting_join_date,
                current_grade_join_date, mobile, email, gender, dob,
                blood_group, join_date, confirmation_date, retirement_date,
                edu_qualification, home_district, present_address, permanent_address,
                nid_number, saved_filename, note, 'Active', db_datetime, session.user.get('user_id', '')
            )
            db.executesql(insert_sql, values)
        except Exception as e:
            print(f"Error during employee insert: {e}")

    return dict()