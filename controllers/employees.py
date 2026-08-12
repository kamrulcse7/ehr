from py4web import URL, action, redirect, request, response
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import flash, session, view_page
from ..core.db import db, db_datetime
from datetime import datetime
import xml.sax.saxutils as xml_escape
import math
import io
import csv
import os
import time

HEADER_MAP = {
    'emp_id': ['official id', 'official_id', 'officialid', 'employee id', 'id', 'empid', 'emp_id', 'employee_id'],
    'emp_name': ['full name', 'name', 'emp_name', 'employee_name', 'employee name'],
    'card_number': ['card number', 'card_number', 'card no', 'cardno', 'rfid'],
    'emp_type': ['employment type', 'emp_type', 'type', 'employment_type'],
    'emp_department': ['department', 'emp_department', 'dept', 'department name'],
    'emp_designation': ['designation', 'emp_designation', 'designation name'],
    'emp_grade': ['grade', 'emp_grade', 'scale'],
    'current_posting_place': ['posting place', 'posting_place', 'current_posting_place', 'posting location', 'posting station'],
    'current_posting_join_date': ['posting join date', 'posting_join_date', 'current_posting_join_date'],
    'current_grade_join_date': ['grade join date', 'grade_join_date', 'current_grade_join_date'],
    'mobile': ['mobile', 'phone', 'contact', 'mobile number', 'mobile_number'],
    'email': ['email', 'email address', 'email_address'],
    'gender': ['gender', 'sex'],
    'dob': ['dob', 'date of birth', 'birth date', 'date_of_birth'],
    'blood_group': ['blood group', 'blood_group', 'blood'],
    'join_date': ['join date', 'join_date', 'joining date', 'joining_date'],
    'confirmation_date': ['confirmation date', 'confirmation_date'],
    'retirement_date': ['retirement_date', 'retirement date'],
    'edu_qualification': ['education', 'educational qualification', 'qualification', 'edu_qualification'],
    'home_district': ['home district', 'home_district', 'district'],
    'present_address': ['present address', 'present_address'],
    'permanent_address': ['permanent address', 'permanent_address'],
    'nid_number': ['nid number', 'nid_number', 'nid'],
    'note': ['note', 'remarks', 'remark'],
    'status_type': ['status', 'status_type', 'status type']
}

ALIAS_MAP = {}
for field, aliases in HEADER_MAP.items():
    for alias in aliases:
        ALIAS_MAP[alias] = field

def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    if date_str.lower() in ('none', 'null', '', 'nat', 'nan'):
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%m/%d/%Y', '%d.%m.%Y'):
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


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


@action("employees/import_directory", method=["GET", "POST"])
@view_page("employees/import_directory.html", title="Import Directory | EMS")
@web_auth_required
def import_directory():
    # Check if downloading template
    if request.query.get("template") == "csv":
        headers = [
            "Official ID", "Full Name", "Card Number", "Employment Type", "Department",
            "Designation", "Grade", "Posting Place", "Posting Join Date", "Grade Join Date",
            "Mobile", "Email", "Gender", "DOB", "Blood Group", "Join Date",
            "Confirmation Date", "Retirement Date", "Education", "Home District",
            "Present Address", "Permanent Address", "NID Number", "Note", "Status"
        ]
        example = [
            "OFF1001", "Abul Kalam", "100200300", "PERMANENT", "Administration",
            "Senior Officer", "Grade-9", "Head Office", "2024-01-01", "2024-01-01",
            "01711000000", "abul.kalam@example.com", "MALE", "1990-05-15", "O+", "2020-02-15",
            "2021-02-15", "2050-05-15", "MBA", "Dhaka", "Dhaka, Bangladesh", "Dhaka, Bangladesh",
            "1234567890123", "Demo note", "ACTIVE"
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example)
        
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename="Personnel_Import_Template.csv"'
        return output.getvalue()

    stats = None
    active_tab = "file"
    if request.method == "POST":
        csv_file = request.files.get("csv_file")
        csv_text = request.forms.get("csv_text")
        
        content = None
        delimiter = ','
        
        if csv_file and csv_file.filename:
            active_tab = "file"
            if not csv_file.filename.lower().endswith('.csv'):
                flash.set("Only CSV files are allowed.", "danger")
                return dict(stats=None, active_tab=active_tab)
                
            try:
                # Check file size (2MB limit)
                csv_file.file.seek(0, 2)
                file_size = csv_file.file.tell()
                csv_file.file.seek(0)
                if file_size > 2 * 1024 * 1024:
                    flash.set("File size exceeds the maximum limit of 2MB.", "danger")
                    return dict(stats=None, active_tab=active_tab)
                
                content = csv_file.file.read().decode('utf-8-sig')
            except Exception as e:
                flash.set(f"Failed to read CSV file: {str(e)}", "danger")
                return dict(stats=None, active_tab=active_tab)
                
        elif csv_text and csv_text.strip():
            active_tab = "text"
            # Check pasted text length (2MB limit)
            if len(csv_text.encode('utf-8')) > 2 * 1024 * 1024:
                flash.set("Pasted content size exceeds the maximum limit of 2MB.", "danger")
                return dict(stats=None, active_tab=active_tab)
                
            content = csv_text.strip()
            # Detect delimiter: if '\t' is found in the first line, use it
            first_line = content.splitlines()[0] if content else ""
            if '\t' in first_line:
                delimiter = '\t'
            elif ';' in first_line and ',' not in first_line:
                delimiter = ';'
                
        else:
            flash.set("Please select a valid CSV file or paste valid data.", "danger")
            return dict(stats=None, active_tab=active_tab)

        try:
            f = io.StringIO(content)
            reader = csv.DictReader(f, delimiter=delimiter)
            
            headers = reader.fieldnames or []
            mapped_headers = {}
            for h in headers:
                h_clean = h.strip().lower()
                field = ALIAS_MAP.get(h_clean)
                if field:
                    mapped_headers[field] = h
            
            if 'emp_id' not in mapped_headers or 'emp_name' not in mapped_headers:
                flash.set("Invalid format. Missing required columns: 'Official ID' and 'Full Name'.", "danger")
                return dict(stats=None, active_tab=active_tab)

            # Check row count limit (1000 rows max)
            rows = list(reader)
            if len(rows) > 1000:
                flash.set("The data contains too many rows. Maximum allowed is 1,000 rows.", "danger")
                return dict(stats=None, active_tab=active_tab)

            stats = {
                "total": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
                "errors": []
            }

            row_num = 1
            
            for row in rows:
                row_num += 1
                stats["total"] += 1
                
                def get_val(field):
                    csv_col = mapped_headers.get(field)
                    if csv_col and csv_col in row:
                        val = row[csv_col]
                        return val.strip() if val else None
                    return None

                emp_id = get_val('emp_id')
                emp_name = get_val('emp_name')
                
                if not emp_id or not emp_name:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "row": row_num,
                        "emp_id": emp_id or "N/A",
                        "error": "Official ID and Full Name are required."
                    })
                    continue

                mobile = get_val('mobile') or ""
                email = get_val('email') or ""
                
                join_date_str = get_val('join_date')
                join_date = parse_date(join_date_str)
                if not join_date:
                    if join_date_str:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "row": row_num,
                            "emp_id": emp_id,
                            "error": f"Invalid Join Date format: '{join_date_str}'"
                        })
                        continue
                    else:
                        join_date = db_datetime.strftime('%Y-%m-%d')

                dob = parse_date(get_val('dob'))
                current_posting_join_date = parse_date(get_val('current_posting_join_date'))
                current_grade_join_date = parse_date(get_val('current_grade_join_date'))
                confirmation_date = parse_date(get_val('confirmation_date'))
                retirement_date = parse_date(get_val('retirement_date'))

                card_number = get_val('card_number')
                emp_type = get_val('emp_type') or "PERMANENT"
                emp_department = get_val('emp_department')
                emp_designation = get_val('emp_designation')
                emp_grade = get_val('emp_grade')
                current_posting_place = get_val('current_posting_place')
                gender = get_val('gender')
                if gender:
                    gender = gender.upper()
                blood_group = get_val('blood_group')
                edu_qualification = get_val('edu_qualification')
                home_district = get_val('home_district')
                present_address = get_val('present_address')
                permanent_address = get_val('permanent_address')
                nid_number = get_val('nid_number')
                note = get_val('note')
                status_type = get_val('status_type') or "ACTIVE"
                if status_type:
                    status_type = status_type.upper()
                
                try:
                    existing = db.executesql("SELECT id FROM employees WHERE emp_id = %s LIMIT 1", [emp_id])
                    
                    if existing:
                        update_sql = """
                        UPDATE employees SET
                            emp_name = %s,
                            card_number = %s,
                            emp_type = %s,
                            emp_department = %s,
                            emp_designation = %s,
                            emp_grade = %s,
                            current_posting_place = %s,
                            current_posting_join_date = %s,
                            current_grade_join_date = %s,
                            mobile = %s,
                            email = %s,
                            gender = %s,
                            dob = %s,
                            blood_group = %s,
                            join_date = %s,
                            confirmation_date = %s,
                            retirement_date = %s,
                            edu_qualification = %s,
                            home_district = %s,
                            present_address = %s,
                            permanent_address = %s,
                            nid_number = %s,
                            note = %s,
                            status_type = %s,
                            updated_on = %s,
                            updated_by = %s
                        WHERE emp_id = %s
                        """
                        values = (
                            emp_name, card_number, emp_type, emp_department, emp_designation, emp_grade,
                            current_posting_place, current_posting_join_date, current_grade_join_date,
                            mobile, email, gender, dob, blood_group, join_date, confirmation_date, retirement_date,
                            edu_qualification, home_district, present_address, permanent_address, nid_number,
                            note, status_type, db_datetime, session.user.get('user_id', ''), emp_id
                        )
                        db.executesql(update_sql, values)
                        stats["updated"] += 1
                    else:
                        insert_sql = """
                        INSERT INTO employees (
                            emp_id, emp_name, card_number, emp_type, emp_department, 
                            emp_designation, emp_grade, current_posting_place, current_posting_join_date, 
                            current_grade_join_date, mobile, email, gender, dob, 
                            blood_group, join_date, confirmation_date, retirement_date, 
                            edu_qualification, home_district, present_address, permanent_address, 
                            nid_number, note, status_type, created_on, created_by
                        ) VALUES (
                            %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s
                        )
                        """
                        values = (
                            emp_id, emp_name, card_number, emp_type, emp_department, emp_designation, emp_grade,
                            current_posting_place, current_posting_join_date, current_grade_join_date,
                            mobile, email, gender, dob, blood_group, join_date, confirmation_date, retirement_date,
                            edu_qualification, home_district, present_address, permanent_address, nid_number,
                            note, status_type, db_datetime, session.user.get('user_id', '')
                        )
                        db.executesql(insert_sql, values)
                        stats["created"] += 1
                        
                except Exception as ex:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "row": row_num,
                        "emp_id": emp_id,
                        "error": str(ex)
                    })

            if stats["failed"] > 0:
                flash.set(f"Import completed with some errors. Succeeded: {stats['created'] + stats['updated']} (Created: {stats['created']}, Updated: {stats['updated']}), Failed: {stats['failed']}", "warning")
            else:
                flash.set(f"Successfully imported {stats['created'] + stats['updated']} records! (Created: {stats['created']}, Updated: {stats['updated']})", "success")

        except Exception as e:
            flash.set(f"Failed to process CSV file: {str(e)}", "danger")

    return dict(stats=stats, active_tab=active_tab)
