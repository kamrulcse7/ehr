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
    'cid': ['company id', 'company_id', 'cid', 'company', 'companyid', 'company_code', 'company code'],
    'emp_id': ['official id', 'official_id', 'officialid', 'employee id', 'id', 'empid', 'emp_id', 'employee_id'],
    'emp_name': ['full name', 'name', 'emp_name', 'employee_name', 'employee name'],
    'card_number': ['card number', 'card_number', 'card no', 'cardno', 'rfid'],
    'emp_type': ['employment type', 'emp_type', 'type', 'employment_type'],
    'emp_department': ['department', 'emp_department', 'dept', 'department name'],
    'emp_designation': ['designation', 'emp_designation', 'designation name'],
    'current_branch_id': ['branch id', 'branch_id', 'current_branch_id', 'branch', 'posting place', 'posting_place', 'current_posting_place', 'posting location', 'posting station'],
    'current_branch_join_date': ['branch join date', 'branch_join_date', 'current_branch_join_date', 'posting join date', 'posting_join_date', 'current_posting_join_date'],
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


@action("employees/empployee_directory")
@view_page("employees/empployee_directory.html", title="Personnel Directory | EMS")
@web_auth_required
def empployee_directory():
    user_cid = session.user.get("cid", "")
    keywords = request.query.get("keywords", "").strip()
    department = request.query.get("department", "").strip()
    status = request.query.get("status", "").strip()
    export_format = request.query.get("export", "").strip().lower()

    # 1. Build SQL WHERE conditions
    where_clauses = ["1=1"]
    params = []

    cid = user_cid if user_cid else request.query.get("cid", "").strip()
    if cid:
        where_clauses.append("e.cid = %s")
        params.append(cid)

    if keywords:
        where_clauses.append("(e.emp_id LIKE %s OR e.emp_name LIKE %s OR e.mobile LIKE %s)")
        search_term = f"%{keywords}%"
        params.extend([search_term, search_term, search_term])

    if department:
        where_clauses.append("e.emp_department = %s")
        params.append(department)

    if status:
        where_clauses.append("e.status_type = %s")
        params.append(status)
    

    where_str = " AND ".join(where_clauses)

    if export_format in ["xlsx", "xls", "csv"]:
        export_sql = f"""
            SELECT e.id, e.cid, e.emp_id, e.emp_name, e.emp_type, e.emp_department, e.emp_designation, e.emp_grade, 
                   e.mobile, e.email, e.gender, e.dob, e.blood_group, e.join_date, e.retirement_date, e.edu_qualification, 
                   e.home_district, e.present_address, e.permanent_address, e.nid_number, e.note, e.status_type
            FROM employees e
            WHERE {where_str} 
            ORDER BY e.id DESC
        """
        export_records = db.executesql(export_sql, params, as_dict=True)
        filename = f"Employee_List_Full_{db_datetime.strftime('%Y%m%d_%H%M%S')}"

        if not user_cid:
            headers = [
                "ID", "Company ID (CID)", "Official ID", "Full Name", "Service Type", "Department", "Designation", "Grade",
                "Mobile Number", "Email Address", "Gender", "Date of Birth",
                "Blood Group", "Joining Date", "Retirement Date", "Educational Qualification", "Home District",
                "Present Address", "Permanent Address", "NID Number", "Remarks", "Status"
            ]
        else:
            headers = [
                "ID", "Official ID", "Full Name", "Service Type", "Department", "Designation", "Grade",
                "Mobile Number", "Email Address", "Gender", "Date of Birth",
                "Blood Group", "Joining Date", "Retirement Date", "Educational Qualification", "Home District",
                "Present Address", "Permanent Address", "NID Number", "Remarks", "Status"
            ]

        # CSV EXPORT
        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for emp in export_records:
                row_vals = [emp.get('id', '')]
                if not user_cid:
                    row_vals.append(emp.get('cid', ''))
                row_vals.extend([
                    emp.get('emp_id', ''), emp.get('emp_name', ''),
                    emp.get('emp_type', ''), emp.get('emp_department', ''), emp.get('emp_designation', ''), emp.get('emp_grade', ''),
                    emp.get('mobile', ''), emp.get('email', ''), emp.get('gender', ''), emp.get('dob', ''),
                    emp.get('blood_group', ''), emp.get('join_date', ''), emp.get('retirement_date', ''),
                    emp.get('edu_qualification', ''), emp.get('home_district', ''), emp.get('present_address', ''), emp.get('permanent_address', ''),
                    emp.get('nid_number', ''), emp.get('note', ''), emp.get('status_type', '')
                ])
                writer.writerow(row_vals)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return output.getvalue()

        # EXCEL (XML) EXPORT
        elif export_format in ["xlsx", "xls"]:
            xml_data = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?mso-application progid="Excel.Sheet"?>',
                '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"',
                ' xmlns:o="urn:schemas-microsoft-com:office:office"',
                ' xmlns:x="urn:schemas-microsoft-com:office:excel"',
                ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">',
                '<Styles>',
                '<Style ss:ID="HeaderStyle"><Font ss:Bold="1" ss:Color="#FFFFFF"/><Interior ss:Color="#1E293B" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center"/></Style>',
                '<Style ss:ID="DataCenter"><Alignment ss:Horizontal="Center"/></Style>',
                '<Style ss:ID="DataLeft"><Alignment ss:Horizontal="Left"/></Style>',
                '</Styles>',
                '<Worksheet ss:Name="Employees Directory">',
                '<Table>',
                '<Row>'
            ]
            for h in headers:
                xml_data.append(f'<Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{xml_escape.escape(h)}</Data></Cell>')
            xml_data.append('</Row>')

            for emp in export_records:
                xml_data.append('<Row>')
                row_fields = [(emp.get('id') or '', 'DataCenter')]
                if not user_cid:
                    row_fields.append((emp.get('cid') or '', 'DataCenter'))
                row_fields.extend([
                    (emp.get('emp_id') or '', 'DataCenter'),
                    (emp.get('emp_name') or '', 'DataLeft'),
                    (emp.get('emp_type') or '', 'DataCenter'), (emp.get('emp_department') or '', 'DataLeft'),
                    (emp.get('emp_designation') or '', 'DataLeft'), (emp.get('emp_grade') or '', 'DataCenter'),
                    (emp.get('mobile') or '', 'DataCenter'), (emp.get('email') or '', 'DataLeft'),
                    (emp.get('gender') or '', 'DataCenter'), (emp.get('dob') or '', 'DataCenter'),
                    (emp.get('blood_group') or '', 'DataCenter'), (emp.get('join_date') or '', 'DataCenter'),
                    (emp.get('retirement_date') or '', 'DataCenter'), (emp.get('edu_qualification') or '', 'DataLeft'),
                    (emp.get('home_district') or '', 'DataLeft'), (emp.get('present_address') or '', 'DataLeft'),
                    (emp.get('permanent_address') or '', 'DataLeft'), (emp.get('nid_number') or '', 'DataCenter'),
                    (emp.get('note') or '', 'DataLeft'), (emp.get('status_type') or '', 'DataCenter')
                ])
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

    count_sql = f"SELECT COUNT(e.id) as total FROM employees e WHERE {where_str}"
    total_items = db.executesql(count_sql, params, as_dict=True)[0]['total']

    records_sql = f"""
        SELECT e.id, e.cid, e.emp_id, e.emp_name, e.emp_designation, e.emp_grade, e.emp_department, e.emp_type, e.email,
               e.current_branch_id, COALESCE(b.branch_name, e.current_branch_id, 'N/A') AS current_posting_place,
               e.mobile, e.home_district, e.status_type, e.blood_group 
        FROM employees e
        LEFT JOIN branches b ON e.current_branch_id = b.branch_id AND e.cid = b.cid
        WHERE {where_str} ORDER BY e.id DESC LIMIT %s OFFSET %s
    """
    employees_list = db.executesql(records_sql, params + [limit, offset], as_dict=True)

    stats_where = ["1=1"]
    stats_params = []
    if cid:
        stats_where.append("cid = %s")
        stats_params.append(cid)

    stats_sql = f"""
        SELECT COUNT(id) as total,
            COUNT(CASE WHEN status_type = 'ACTIVE' THEN 1 END) as active,
            COUNT(CASE WHEN status_type = 'PROBATIONARY' THEN 1 END) as probationary,
            COUNT(CASE WHEN status_type = 'INACTIVE' THEN 1 END) as inactive
        FROM employees
        WHERE {" AND ".join(stats_where)}
    """
    stats_res = db.executesql(stats_sql, stats_params, as_dict=True)[0]

    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    start_item = offset + 1 if total_items > 0 else 0
    end_item = min(offset + limit, total_items)

    pagination = {
        "current_page": page, "total_pages": total_pages,
        "total_items": total_items, "start_item": start_item,
        "end_item": end_item, "limit": limit
    }

    return dict(employees=employees_list, pagination=pagination, stats=stats_res, user_cid=user_cid)



@action("employees/add_directory", method=["GET", "POST"])
@view_page("employees/add_directory.html", title="Add Directory | EMS")
@web_auth_required
def add_directory():
    user_cid = session.user.get("cid", "")
    form_data = {}

    if request.method == "POST":
        form_data = dict(request.forms)
        try:
            def clean_val(val):
                val = str(val).strip() if val else None
                return val if val != "" else None

            cid = user_cid if user_cid else clean_val(request.forms.get("cid"))
            if not cid:
                flash.set("Company ID (CID) is required.", "danger")
                return dict(user_cid=user_cid, form_data=form_data)

            # Validate CID against companies master table if user is System Admin
            if not user_cid:
                comp_check = db.executesql("SELECT cid FROM companies WHERE cid = %s LIMIT 1", [cid.upper()], as_dict=True)
                if not comp_check:
                    flash.set(f"Invalid CID '{cid}'. Company does not exist.", "danger")
                    return dict(user_cid=user_cid, form_data=form_data)
                cid = comp_check[0]['cid']

            emp_name = clean_val(request.forms.get("emp_name"))
            mobile = clean_val(request.forms.get("mobile"))
            email = clean_val(request.forms.get("email"))
            nid_number = clean_val(request.forms.get("nid_number"))
            dob = clean_val(request.forms.get("dob"))
            gender = clean_val(request.forms.get("gender"))
            blood_group = clean_val(request.forms.get("blood_group"))
            edu_qualification = clean_val(request.forms.get("edu_qualification"))

            emp_id = clean_val(request.forms.get("emp_id"))
            emp_type = clean_val(request.forms.get("emp_type"))
            emp_department = clean_val(request.forms.get("emp_department"))
            emp_designation = clean_val(request.forms.get("emp_designation"))
            emp_grade = clean_val(request.forms.get("emp_grade"))
            join_date = clean_val(request.forms.get("join_date"))
            retirement_date = clean_val(request.forms.get("retirement_date"))

            home_district = clean_val(request.forms.get("home_district"))
            present_address = clean_val(request.forms.get("present_address"))
            permanent_address = clean_val(request.forms.get("permanent_address"))
            note = clean_val(request.forms.get("note"))
            
            # Check duplicate Official ID for CID
            emp_check = db.executesql("SELECT id FROM employees WHERE cid = %s AND emp_id = %s LIMIT 1", [cid, emp_id])
            if emp_check:
                flash.set(f"'{emp_id}' already exists.", "danger")
                return dict(user_cid=user_cid, form_data=form_data)

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
                cid, emp_id, emp_name, emp_type, emp_department, 
                emp_designation, emp_grade, mobile, email, gender, dob, 
                blood_group, join_date, retirement_date, 
                edu_qualification, home_district, present_address, permanent_address, 
                nid_number, photo_url, note, status_type, created_on, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s
            )
            """
            user_id = session.user.get('user_id', '') if (session and session.user) else ''
            values = (
                cid, emp_id, emp_name, emp_type, emp_department,
                emp_designation, emp_grade, mobile, email, gender, dob,
                blood_group, join_date, retirement_date,
                edu_qualification, home_district, present_address, permanent_address,
                nid_number, saved_filename, note, 'ACTIVE', db_datetime, user_id
            )
            db.executesql(insert_sql, values)
            db.commit()
            flash.set("Added successfully!", "success")
            # Clear form fields on success
            form_data = {}
        except Exception as e:
            flash.set(f"Failed to add: {str(e)}", "danger")
            return dict(user_cid=user_cid, form_data=form_data)

    return dict(user_cid=user_cid, form_data=form_data)


@action("employees/import_directory", method=["GET", "POST"])
@view_page("employees/import_directory.html", title="Import Directory | EMS")
@web_auth_required
def import_directory():
    user_cid = session.user.get("cid", "")
    # Check if downloading template
    if request.query.get("template") == "csv":
        if not user_cid:
            headers = [
                "Company ID (CID)", "Official ID", "Full Name", "Employment Type", "Department",
                "Designation", "Grade", "Posting Place", "Posting Join Date", "Grade Join Date",
                "Mobile", "Email", "Gender", "DOB", "Blood Group", "Join Date",
                "Confirmation Date", "Retirement Date", "Education", "Home District",
                "Present Address", "Permanent Address", "NID Number", "Note", "Status"
            ]
            example = [
                "EON", "OFF1001", "Abul Kalam", "PERMANENT", "Administration",
                "Senior Officer", "Grade-9", "Head Office", "2024-01-01", "2024-01-01",
                "01711000000", "abul.kalam@example.com", "MALE", "1990-05-15", "O+", "2020-02-15",
                "2021-02-15", "2050-05-15", "MBA", "Dhaka", "Dhaka, Bangladesh", "Dhaka, Bangladesh",
                "1234567890123", "Demo note", "ACTIVE"
            ]
        else:
            headers = [
                "Official ID", "Full Name", "Employment Type", "Department",
                "Designation", "Grade", "Posting Place", "Posting Join Date", "Grade Join Date",
                "Mobile", "Email", "Gender", "DOB", "Blood Group", "Join Date",
                "Confirmation Date", "Retirement Date", "Education", "Home District",
                "Present Address", "Permanent Address", "NID Number", "Note", "Status"
            ]
            example = [
                "OFF1001", "Abul Kalam", "PERMANENT", "Administration",
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
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
                
            try:
                # Check file size (2MB limit)
                csv_file.file.seek(0, 2)
                file_size = csv_file.file.tell()
                csv_file.file.seek(0)
                if file_size > 2 * 1024 * 1024:
                    flash.set("File size exceeds the maximum limit of 2MB.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
                
                content = csv_file.file.read().decode('utf-8-sig')
            except Exception as e:
                flash.set(f"Failed to read CSV file: {str(e)}", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
                
        elif csv_text and csv_text.strip():
            active_tab = "text"
            # Check pasted text length (2MB limit)
            if len(csv_text.encode('utf-8')) > 2 * 1024 * 1024:
                flash.set("Pasted content size exceeds the maximum limit of 2MB.", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
                
            content = csv_text.strip()
            # Detect delimiter: if '\t' is found in the first line, use it
            first_line = content.splitlines()[0] if content else ""
            if '\t' in first_line:
                delimiter = '\t'
            elif ';' in first_line and ',' not in first_line:
                delimiter = ';'
                
        else:
            flash.set("Please select a valid CSV file or paste valid data.", "danger")
            return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

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
            
            if not user_cid:
                if 'cid' not in mapped_headers or 'emp_id' not in mapped_headers or 'emp_name' not in mapped_headers:
                    flash.set("Invalid format. Missing required columns for System Admin: 'Company ID (CID)', 'Official ID', and 'Full Name'.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
            else:
                if 'emp_id' not in mapped_headers or 'emp_name' not in mapped_headers:
                    flash.set("Invalid format. Missing required columns: 'Official ID' and 'Full Name'.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

            # Check row count limit (1000 rows max)
            rows = list(reader)
            if len(rows) > 1000:
                flash.set("The data contains too many rows. Maximum allowed is 1,000 rows.", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

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
                row_cid = user_cid if user_cid else get_val('cid')
                
                if not emp_id or not emp_name:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "row": row_num,
                        "emp_id": emp_id or "N/A",
                        "error": "Official ID and Full Name are required."
                    })
                    continue

                if not row_cid:
                    stats["failed"] += 1
                    stats["errors"].append({
                        "row": row_num,
                        "emp_id": emp_id,
                        "error": "Company ID (CID) is required."
                    })
                    continue

                if not user_cid:
                    comp_check = db.executesql("SELECT cid FROM companies WHERE cid = %s LIMIT 1", [row_cid.upper()], as_dict=True)
                    if not comp_check:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "row": row_num,
                            "emp_id": emp_id,
                            "error": f"Invalid CID '{row_cid}'. Company does not exist."
                        })
                        continue
                    row_cid = comp_check[0]['cid']

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

                emp_type = get_val('emp_type') or "PERMANENT"
                emp_department = get_val('emp_department')
                emp_designation = get_val('emp_designation')
                emp_grade = get_val('emp_grade')
                current_branch_id = get_val('current_branch_id') or get_val('current_posting_place')
                current_branch_join_date = parse_date(get_val('current_branch_join_date') or get_val('current_posting_join_date'))
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
                    existing = db.executesql("SELECT id FROM employees WHERE cid = %s AND emp_id = %s LIMIT 1", [row_cid, emp_id])
                    
                    if existing:
                        update_sql = """
                        UPDATE employees SET
                            emp_name = %s,
                            emp_type = %s,
                            emp_department = %s,
                            emp_designation = %s,
                            emp_grade = %s,
                            current_branch_id = %s,
                            current_branch_join_date = %s,
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
                        WHERE cid = %s AND emp_id = %s
                        """
                        values = (
                            emp_name, emp_type, emp_department, emp_designation, emp_grade,
                            current_branch_id, current_branch_join_date, current_grade_join_date,
                            mobile, email, gender, dob, blood_group, join_date, confirmation_date, retirement_date,
                            edu_qualification, home_district, present_address, permanent_address, nid_number,
                            note, status_type, db_datetime, session.user.get('user_id', ''), row_cid, emp_id
                        )
                        db.executesql(update_sql, values)
                        stats["updated"] += 1
                    else:
                        insert_sql = """
                        INSERT INTO employees (
                            cid, emp_id, emp_name, emp_type, emp_department, 
                            emp_designation, emp_grade, current_branch_id, current_branch_join_date, 
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
                            row_cid, emp_id, emp_name, emp_type, emp_department, emp_designation, emp_grade,
                            current_branch_id, current_branch_join_date, current_grade_join_date,
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

            db.commit()
            if stats["failed"] > 0:
                flash.set(f"Import completed with some errors. Succeeded: {stats['created'] + stats['updated']} (Created: {stats['created']}, Updated: {stats['updated']}), Failed: {stats['failed']}", "warning")
            else:
                flash.set(f"Successfully imported {stats['created'] + stats['updated']} records! (Created: {stats['created']}, Updated: {stats['updated']})", "success")

        except Exception as e:
            flash.set(f"Failed to process CSV file: {str(e)}", "danger")

    return dict(stats=stats, active_tab=active_tab, user_cid=user_cid)


@action("employees/postings_transfers")
@view_page("employees/postings_transfers.html", title="Postings & Transfers | EMS")
@web_auth_required
def postings_transfers():
    keywords = request.query.get("keywords", "").strip()
    status_type = request.query.get("status_type", "").strip()
    transfer_type = request.query.get("transfer_type", "").strip()
    export_format = request.query.get("export", "").strip().lower()

    where_clauses = ["1=1"]
    params = []

    if keywords:
        where_clauses.append("(t.emp_id LIKE %s OR e.emp_name LIKE %s OR t.transfer_order_no LIKE %s OR t.to_branch_id LIKE %s)")
        search_term = f"%{keywords}%"
        params.extend([search_term, search_term, search_term, search_term])

    if status_type:
        where_clauses.append("t.joining_status = %s")
        params.append(status_type)

    if transfer_type:
        where_clauses.append("t.transfer_type = %s")
        params.append(transfer_type)

    where_str = " AND ".join(where_clauses)

    # Export Excel / CSV Handling
    if export_format in ["xlsx", "xls", "csv"]:
        export_sql = f"""
            SELECT t.id, t.emp_id, e.emp_name, t.transfer_order_no, t.transfer_type,
                   t.from_branch_id, t.to_branch_id,
                   COALESCE(fb.branch_name, t.from_branch_id) AS from_posting_place,
                   COALESCE(tb.branch_name, t.to_branch_id) AS to_posting_place,
                   t.from_department, t.to_department,
                   t.from_designation, t.to_designation, t.order_date, t.expected_joining_date,
                   t.joining_status, t.approved_by, t.transfer_reason
            FROM employee_transfers t
            LEFT JOIN employees e ON t.emp_id = e.emp_id AND t.cid = e.cid
            LEFT JOIN branches fb ON t.from_branch_id = fb.branch_id AND t.cid = fb.cid
            LEFT JOIN branches tb ON t.to_branch_id = tb.branch_id AND t.cid = tb.cid
            WHERE {where_str} 
            ORDER BY t.id DESC
        """
        export_records = db.executesql(export_sql, params, as_dict=True)
        filename = f"Transfer_Orders_List_{db_datetime.strftime('%Y%m%d_%H%M%S')}"

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "ID", "Official ID", "Employee Name", "Order No", "Transfer Type",
                "From Branch", "To Branch", "From Department", "To Department",
                "From Designation", "To Designation", "Order Date", "Expected Joining Date",
                "Status", "Approved By", "Remarks"
            ])
            for rec in export_records:
                writer.writerow([
                    rec.get('id'), rec.get('emp_id'), rec.get('emp_name'), rec.get('transfer_order_no'), rec.get('transfer_type'),
                    rec.get('from_posting_place'), rec.get('to_posting_place'), rec.get('from_department'), rec.get('to_department'),
                    rec.get('from_designation'), rec.get('to_designation'), rec.get('order_date'), rec.get('expected_joining_date'),
                    rec.get('joining_status'), rec.get('approved_by'), rec.get('transfer_reason')
                ])
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return output.getvalue()

        elif export_format in ["xlsx", "xls"]:
            headers_list = [
                "ID", "Official ID", "Employee Name", "Order No", "Transfer Type",
                "From Branch", "To Branch", "From Department", "To Department",
                "Order Date", "Expected Joining Date", "Status", "Remarks"
            ]
            xml_data = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?mso-application progid="Excel.Sheet"?>',
                '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"',
                ' xmlns:o="urn:schemas-microsoft-com:office:office"',
                ' xmlns:x="urn:schemas-microsoft-com:office:excel"',
                ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">',
                '<Styles>',
                '<Style ss:ID="HeaderStyle"><Font ss:Bold="1" ss:Color="#FFFFFF"/><Interior ss:Color="#1E293B" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center"/></Style>',
                '<Style ss:ID="DataCenter"><Alignment ss:Horizontal="Center"/></Style>',
                '<Style ss:ID="DataLeft"><Alignment ss:Horizontal="Left"/></Style>',
                '</Styles>',
                '<Worksheet ss:Name="Transfer Orders">',
                '<Table>',
                '<Row>'
            ]
            for h in headers_list:
                xml_data.append(f'<Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{xml_escape.escape(h)}</Data></Cell>')
            xml_data.append('</Row>')

            for rec in export_records:
                xml_data.append('<Row>')
                row_fields = [
                    (rec.get('id') or '', 'DataCenter'), (rec.get('emp_id') or '', 'DataCenter'),
                    (rec.get('emp_name') or '', 'DataLeft'), (rec.get('transfer_order_no') or '', 'DataCenter'),
                    (rec.get('transfer_type') or '', 'DataCenter'), (rec.get('from_posting_place') or '', 'DataLeft'),
                    (rec.get('to_posting_place') or '', 'DataLeft'), (rec.get('from_department') or '', 'DataLeft'),
                    (rec.get('to_department') or '', 'DataLeft'), (rec.get('order_date') or '', 'DataCenter'),
                    (rec.get('expected_joining_date') or '', 'DataCenter'), (rec.get('joining_status') or '', 'DataCenter'),
                    (rec.get('transfer_reason') or '', 'DataLeft')
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

    count_sql = f"""
        SELECT COUNT(t.id) as total 
        FROM employee_transfers t
        LEFT JOIN employees e ON t.emp_id = e.emp_id
        WHERE {where_str}
    """
    total_items = db.executesql(count_sql, params, as_dict=True)[0]['total']

    transfers_sql = f"""
        SELECT t.*, e.emp_name, e.photo_url, e.emp_designation as current_emp_designation, e.emp_department as current_emp_dept,
               COALESCE(fb.branch_name, t.from_branch_id) AS from_posting_place,
               COALESCE(tb.branch_name, t.to_branch_id) AS to_posting_place
        FROM employee_transfers t
        LEFT JOIN employees e ON t.emp_id = e.emp_id AND t.cid = e.cid
        LEFT JOIN branches fb ON t.from_branch_id = fb.branch_id AND t.cid = fb.cid
        LEFT JOIN branches tb ON t.to_branch_id = tb.branch_id AND t.cid = tb.cid
        WHERE {where_str}
        ORDER BY t.id DESC LIMIT %s OFFSET %s
    """
    transfers_list = db.executesql(transfers_sql, params + [limit, offset], as_dict=True)

    stats_sql = """
        SELECT COUNT(id) as total,
            COUNT(CASE WHEN joining_status IN ('JOINED', 'COMPLETED') THEN 1 END) as joined,
            COUNT(CASE WHEN joining_status IN ('PENDING', 'RELEASED') THEN 1 END) as pending,
            COUNT(CASE WHEN transfer_type = 'PROMOTION' THEN 1 END) as promotions
        FROM employee_transfers
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

    return dict(transfers=transfers_list, pagination=pagination, stats=stats_res)


@action("employees/add_transfer", method=["GET", "POST"])
@view_page("employees/add_transfer.html", title="Issue Transfer Order | EMS")
@web_auth_required
def add_transfer():
    lookup_id = request.query.get("lookup_id", "").strip()
    emp = None
    if lookup_id:
        emp_res = db.executesql(
            "SELECT emp_id, emp_name, emp_designation, emp_department, current_branch_id, emp_grade FROM employees WHERE emp_id = %s AND status_type = 'ACTIVE' LIMIT 1",
            [lookup_id],
            as_dict=True
        )
        emp = emp_res[0] if emp_res else None

    if request.method == "POST":
        try:
            def clean_val(val):
                val = str(val).strip() if val else None
                return val if val != "" else None

            emp_id = clean_val(request.forms.get("emp_id"))
            transfer_order_no = clean_val(request.forms.get("transfer_order_no"))
            transfer_type = clean_val(request.forms.get("transfer_type")) or "ADMINISTRATIVE"
            from_branch_id = clean_val(request.forms.get("from_branch_id")) or clean_val(request.forms.get("from_posting_place"))
            to_branch_id = clean_val(request.forms.get("to_branch_id")) or clean_val(request.forms.get("to_posting_place"))
            from_department = clean_val(request.forms.get("from_department"))
            to_department = clean_val(request.forms.get("to_department"))
            from_designation = clean_val(request.forms.get("from_designation"))
            to_designation = clean_val(request.forms.get("to_designation"))
            from_grade = clean_val(request.forms.get("from_grade"))
            to_grade = clean_val(request.forms.get("to_grade"))
            order_date = clean_val(request.forms.get("order_date")) or db_datetime.strftime('%Y-%m-%d')
            release_date = clean_val(request.forms.get("release_date"))
            expected_joining_date = clean_val(request.forms.get("expected_joining_date"))
            actual_joining_date = clean_val(request.forms.get("actual_joining_date"))
            transfer_reason = clean_val(request.forms.get("transfer_reason"))
            note = clean_val(request.forms.get("note"))
            joining_status = clean_val(request.forms.get("joining_status")) or "PENDING"

            status_type = "COMPLETED" if joining_status in ["JOINED", "COMPLETED"] else joining_status

            if emp_id and transfer_order_no and to_branch_id:
                if not from_branch_id or not from_department or not from_designation or not from_grade:
                    emp_curr = db.executesql(
                        "SELECT current_branch_id, emp_department, emp_designation, emp_grade FROM employees WHERE emp_id = %s LIMIT 1",
                        [emp_id],
                        as_dict=True
                    )
                    if emp_curr:
                        ec = emp_curr[0]
                        if not from_branch_id: from_branch_id = ec.get('current_branch_id') or "HO_DHAKA"
                        if not from_department: from_department = ec.get('emp_department')
                        if not from_designation: from_designation = ec.get('emp_designation')
                        if not from_grade: from_grade = ec.get('emp_grade')
                
                if not from_branch_id:
                    from_branch_id = "HO_DHAKA"

                insert_sql = """
                INSERT INTO employee_transfers (
                    cid, emp_id, transfer_order_no, transfer_type, transfer_reason,
                    from_branch_id, to_branch_id, from_department, to_department,
                    from_designation, to_designation, from_grade, to_grade, order_date, release_date,
                    expected_joining_date, actual_joining_date, joining_status,
                    note, status_type, created_on, created_by
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
                """
                cid = session.user.get('cid', 'BADC') if (session and session.user) else 'BADC'
                user_id = session.user.get('user_id', '') if (session and session.user) else ''
                values = (
                    cid, emp_id, transfer_order_no, transfer_type, transfer_reason,
                    from_branch_id, to_branch_id, from_department, to_department,
                    from_designation, to_designation, from_grade, to_grade, order_date, release_date,
                    expected_joining_date, actual_joining_date, joining_status,
                    note, status_type, db_datetime, user_id
                )
                db.executesql(insert_sql, values)

                if joining_status in ['JOINED', 'COMPLETED']:
                    update_emp_sql = """
                    UPDATE employees SET
                        current_branch_id = %s,
                        emp_department = COALESCE(%s, emp_department),
                        emp_designation = COALESCE(%s, emp_designation),
                        current_branch_join_date = COALESCE(%s, current_branch_join_date)
                    WHERE emp_id = %s
                    """
                    db.executesql(update_emp_sql, (to_branch_id, to_department, to_designation, actual_joining_date or expected_joining_date or order_date, emp_id))

                db.commit()
                flash.set("Transfer Order issued successfully!", "success")
                emp=None
            else:
                flash.set("Please fill in all required fields marked with *.", "danger")
        except Exception as e:
            print(f"Error creating transfer order: {e}")
            flash.set(f"Failed to issue transfer order: {str(e)}", "danger")

    return dict(emp=emp)


@action("employees/import_transfer", method=["GET", "POST"])
@view_page("employees/import_transfer.html", title="Import Postings & Transfers | EMS")
@web_auth_required
def import_transfer():

    if request.query.get("template") == "csv":
        headers = [
            "Official ID", "Transfer Order No", "Transfer Type", "From Posting", "To Posting",
            "From Department", "To Department", "Order Date", "Expected Joining Date", "Status", "Remarks"
        ]
        example = [
            "EMP-00101", "BADC/TR-2026/001", "ADMINISTRATIVE", "Head Office", "Bogura Regional Office",
            "Administration", "Irrigation Wing", "2026-08-01", "2026-08-15", "PENDING", "Routine rotation transfer"
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename="Posting_Transfer_Import_Template.csv"'
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
                content = csv_file.file.read().decode('utf-8-sig')
            except Exception as e:
                flash.set(f"Failed to read CSV file: {str(e)}", "danger")
                return dict(stats=None, active_tab=active_tab)
        elif csv_text and csv_text.strip():
            active_tab = "text"
            content = csv_text.strip()
            first_line = content.splitlines()[0] if content else ""
            if '\t' in first_line: delimiter = '\t'
            elif ';' in first_line and ',' not in first_line: delimiter = ';'
        else:
            flash.set("Please select a valid CSV file or paste valid data.", "danger")
            return dict(stats=None, active_tab=active_tab)

        try:
            f = io.StringIO(content)
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)

            stats = {"total": 0, "created": 0, "updated": 0, "failed": 0, "errors": []}
            row_num = 1

            for row in rows:
                row_num += 1
                stats["total"] += 1
                
                # Extract fields
                emp_id = row.get("Official ID") or row.get("emp_id") or row.get("Official ID")
                order_no = row.get("Transfer Order No") or row.get("order_no") or row.get("Order No")
                to_branch = row.get("To Branch") or row.get("to_branch_id") or row.get("To Posting") or row.get("to_posting_place")

                if not emp_id or not order_no or not to_branch:
                    stats["failed"] += 1
                    stats["errors"].append({"row": row_num, "emp_id": emp_id or "N/A", "error": "Official ID, Order No, and To Branch are required."})
                    continue

                transfer_type = row.get("Transfer Type") or "ADMINISTRATIVE"
                from_branch = row.get("From Branch") or row.get("from_branch_id") or row.get("From Posting") or "HO_DHAKA"
                from_dept = row.get("From Department") or ""
                to_dept = row.get("To Department") or ""
                order_date = parse_date(row.get("Order Date")) or db_datetime.strftime('%Y-%m-%d')
                expected_joining_date = parse_date(row.get("Expected Joining Date"))
                status = (row.get("Status") or "PENDING").upper()
                remarks = row.get("Remarks") or ""

                try:
                    cid = session.user.get('cid', 'BADC') if (session and session.user) else 'BADC'
                    insert_sql = """
                    INSERT INTO employee_transfers (
                        cid, emp_id, transfer_order_no, transfer_type, transfer_reason,
                        from_branch_id, to_branch_id, from_department, to_department,
                        order_date, expected_joining_date, joining_status, approved_by, approved_on, status_type, created_on, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    db.executesql(insert_sql, (
                        cid, emp_id, order_no, transfer_type, remarks,
                        from_branch, to_branch, from_dept, to_dept,
                        order_date, expected_joining_date, status, "Admin Authority", db_datetime, status, db_datetime, session.user.get('user_id', '')
                    ))
                    stats["created"] += 1

                    if status in ['JOINED', 'COMPLETED']:
                        update_emp = "UPDATE employees SET current_branch_id = %s WHERE emp_id = %s"
                        db.executesql(update_emp, (to_branch, emp_id))
                except Exception as ex:
                    stats["failed"] += 1
                    stats["errors"].append({"row": row_num, "emp_id": emp_id, "error": str(ex)})

            db.commit()
            if stats["failed"] > 0:
                flash.set(f"Import completed with warnings. Created: {stats['created']}, Failed: {stats['failed']}", "warning")
            else:
                flash.set(f"Successfully imported {stats['created']} transfer orders!", "success")

        except Exception as e:
            flash.set(f"Failed to process CSV file: {str(e)}", "danger")

    return dict(stats=stats, active_tab=active_tab)

