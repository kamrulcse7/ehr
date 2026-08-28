from py4web import URL, action, redirect, request, response
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page
import math
import io
import csv
from datetime import datetime

all_roles = [
    {
        "role_id": "ROLE_SUPER_ADMIN",
        "role_name": "Super Admin",
        "description": "Full system access",
        "permissions": [
            {
                "module_group": "Administration",
                "modules": [
                    {
                        "module_id": "user_mgmt",
                        "module_name": "User Management",
                        "description": "User Management",
                        "module_icon": "manage_accounts",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                    {
                        "module_id": "role_mgmt",
                        "module_name": "Role Management",
                        "description": "Role Management",
                        "module_icon": "admin_panel_settings",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                ],
            },
            {
                "module_group": "Employees",
                "modules": [
                    {
                        "module_id": "emp_mgmt",
                        "module_name": "Employee Management",
                        "description": "Employee Management",
                        "module_icon": "badge",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                    {
                        "module_id": "transfer_mgmt",
                        "module_name": "Transfer Management",
                        "description": "Transfer Management",
                        "module_icon": "swap_horiz",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                ],
            },
            {
                "module_group": "Organization",
                "modules": [
                    {
                        "module_id": "department_mgmt",
                        "module_name": "Department Management",
                        "description": "Department Management",
                        "module_icon": "domain",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                    {
                        "module_id": "designation_mgmt",
                        "module_name": "Designation Management",
                        "description": "Designation Management",
                        "module_icon": "military_tech",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                    {
                        "module_id": "branch_mgmt",
                        "module_name": "Branch Management",
                        "description": "Branch Management",
                        "module_icon": "store",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    },
                ],
            },
            {
                "module_group": "Analytics & System",
                "modules": [
                    {
                        "module_id": "report_view",
                        "module_name": "Report View",
                        "description": "Report View",
                        "module_icon": "analytics",
                        "can_view": True,
                        "can_create": False,
                        "can_edit": False,
                        "can_delete": False,
                        "can_export": True,
                        "can_import": False,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    }
                ],
            },
        
        ],
    },
    {
        "role_id": "ROLE_SYS_MANAGER",
        "role_name": "System Manager",
        "description": "System Manager",
        "permissions": [
            {
                "module_group": "Organization",
                "modules": [
                    {
                        "module_id": "branch_mgmt",
                        "module_name": "Branch Management",
                        "description": "Branch Management",
                        "module_icon": "store",
                        "can_view": True,
                        "can_create": True,
                        "can_edit": True,
                        "can_delete": True,
                        "can_export": True,
                        "can_import": True,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    }
                ],
            },
            {
                "module_group": "Analytics & System",
                "modules": [
                    {
                        "module_id": "report_view",
                        "module_name": "Report View",
                        "description": "Report View",
                        "module_icon": "analytics",
                        "can_view": True,
                        "can_create": False,
                        "can_edit": False,
                        "can_delete": False,
                        "can_export": True,
                        "can_import": False,
                        "can_approve": True,
                        "can_reject": True,
                        "can_view_sensitive": True,
                    }
                ],
            },
        ],
    },
]



@action("administration/companies", method=["GET", "POST"])
@view_page("administration/companies.html", title="Company Management | Administration")
@web_auth_required
def companies():
    user_cid = session.user.get("cid", "")
    
    # 1. Fetch Summary Stats
    stats_sql = """
    SELECT 
        COUNT(*) AS total,
        SUM(CASE WHEN status_type = 'ACTIVE' THEN 1 ELSE 0 END) AS active,
        SUM(CASE WHEN status_type != 'ACTIVE' THEN 1 ELSE 0 END) AS inactive
    FROM companies;
    """
    stats_rows = db.executesql(stats_sql, as_dict=True)
    stats = stats_rows[0] if stats_rows else {"total": 0, "active": 0, "inactive": 0}

    # 2. Filter & Search Parameters
    keywords = (request.query.get("keywords") or "").strip()
    status = (request.query.get("status") or "").strip()
    export_fmt = (request.query.get("export") or "").strip()

    where_clauses = ["1=1"]
    placeholders = []

    if keywords:
        where_clauses.append("(cid LIKE %s OR company_name LIKE %s OR legal_name LIKE %s OR email LIKE %s OR phone LIKE %s OR city LIKE %s)")
        search_term = f"%{keywords}%"
        placeholders.extend([search_term, search_term, search_term, search_term, search_term, search_term])

    if status:
        where_clauses.append("status_type = %s")
        placeholders.append(status)

    where_sql = " AND ".join(where_clauses)

    # 3. Export CSV/Excel
    if export_fmt in ("csv", "xlsx"):
        export_sql = f"""
        SELECT 
            cid, company_name, legal_name, email, phone, website,
            address_line1, address_line2, city, state, country, postal_code,
            timezone, language_code, fiscal_year_start_month, status_type, note,
            created_on, created_by
        FROM companies 
        WHERE {where_sql} 
        ORDER BY id DESC
        """
        export_rows = db.executesql(export_sql, placeholders=placeholders, as_dict=True)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "CID", "Company Name", "Legal Name", "Email", "Phone", "Website",
            "Address Line 1", "Address Line 2", "City", "State", "Country", "Postal Code",
            "Timezone", "Language Code", "Fiscal Year Start Month", "Status", "Note / Remarks",
            "Created On", "Created By"
        ])
        for r in export_rows:
            writer.writerow([
                r.get("cid"), r.get("company_name"), r.get("legal_name"), r.get("email"), r.get("phone"), r.get("website"),
                r.get("address_line1"), r.get("address_line2"), r.get("city"), r.get("state"), r.get("country"), r.get("postal_code"),
                r.get("timezone"), r.get("language_code"), r.get("fiscal_year_start_month"), r.get("status_type"), r.get("note"),
                r.get("created_on"), r.get("created_by")
            ])
        
        filename = f"Companies_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return output.getvalue()

    # 4. Pagination
    try:
        page = max(1, int(request.query.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = int(request.query.get("limit", 10))
        if limit not in [10, 25, 50, 100]:
            limit = 10
    except (ValueError, TypeError):
        limit = 10

    count_sql = f"SELECT COUNT(*) as cnt FROM companies WHERE {where_sql}"
    total_count_rows = db.executesql(count_sql, placeholders=placeholders, as_dict=True)
    total_filtered = total_count_rows[0]["cnt"] if total_count_rows else 0

    total_pages = max(1, math.ceil(total_filtered / limit))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * limit

    data_sql = f"SELECT * FROM companies WHERE {where_sql} ORDER BY id DESC LIMIT %s OFFSET %s"
    query_params = placeholders + [limit, offset]
    paginated_companies = db.executesql(data_sql, placeholders=query_params, as_dict=True)

    start_idx = offset
    end_idx = start_idx + len(paginated_companies)

    pagination = {
        "current_page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_items": total_filtered,
        "start_item": start_idx + 1 if total_filtered > 0 else 0,
        "end_item": end_idx,
    }

    return dict(
        user_cid=user_cid,
        companies=paginated_companies,
        stats=stats,
        pagination=pagination,
    )


@action("administration/roles_permisions")
@view_page("administration/roles_permisions.html")
@web_auth_required
def roles_permisions():
    return dict(all_roles=all_roles)



@action("administration/roles_permisions_manage")
@view_page("administration/roles_permisions_manage.html")
@web_auth_required
def roles_permisions_manage():
    role_id = request.params.get("role_id")

    module_groups = [
         {
            "module_group": "Administration",
            "modules": [
                {
                    "module_id": "user_mgmt",
                    "module_name": "User Management",
                    "description": "User Management",
                    "module_icon": "manage_accounts",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
                {
                    "module_id": "role_mgmt",
                    "module_name": "Role Management",
                    "description": "Role Management",
                    "module_icon": "admin_panel_settings",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
            ],
        },
        {
            "module_group": "Employees",
            "modules": [
                {
                    "module_id": "emp_mgmt",
                    "module_name": "Employee Management",
                    "description": "Employee Management",
                    "module_icon": "badge",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
                {
                    "module_id": "transfer_mgmt",
                    "module_name": "Transfer Management",
                    "description": "Transfer Management",
                    "module_icon": "swap_horiz",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
            ],
        },
        {
            "module_group": "Organization",
            "modules": [
                {
                    "module_id": "department_mgmt",
                    "module_name": "Department Management",
                    "description": "Department Management",
                    "module_icon": "domain",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
                {
                    "module_id": "designation_mgmt",
                    "module_name": "Designation Management",
                    "description": "Designation Management",
                    "module_icon": "military_tech",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
                {
                    "module_id": "branch_mgmt",
                    "module_name": "Branch Management",
                    "description": "Branch Management",
                    "module_icon": "store",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                },
            ],
        },
        {
            "module_group": "Analytics & System",
            "modules": [
                {
                    "module_id": "report_view",
                    "module_name": "Report View",
                    "description": "Report View",
                    "module_icon": "analytics",
                    "can_view": False,
                    "can_create": False,
                    "can_edit": False,
                    "can_delete": False,
                    "can_export": False,
                    "can_import": False,
                    "can_approve": False,
                    "can_reject": False,
                    "can_view_sensitive": False,
                }
            ],
        },
    ]

    role_name = ""
    description = ""

    if role_id:
        selected_role = next(
            (r for r in all_roles if str(r["role_id"]) == str(role_id)), None
        )

        if selected_role:
            role_name = selected_role.get("role_name", "")
            description = selected_role.get("description", "")

            perm_map = {
                mod["module_id"]: mod
                for group in selected_role.get("permissions", [])
                for mod in group.get("modules", [])
            }

            for group in module_groups:
                for mod in group.get("modules", []):
                    mod_id = mod["module_id"]
                    if mod_id in perm_map:
                        saved_mod = perm_map[mod_id]
                        for key in mod:
                            if key.startswith("can_"):
                                mod[key] = saved_mod.get(key, False)
    return dict(
        role_id=role_id,
        role_name=role_name,
        description=description,
        module_groups=module_groups,
    )

@action("administration/users")
@view_page("administration/users.html", title="User Management | Administration")
@web_auth_required
def users():
    user_records_sql = """
        SELECT 
            u.id, 
            u.user_id, 
            u.user_name, 
            COALESCE(u.email, '--') AS user_email, 
            COALESCE(e.emp_department, '--') AS department, 
            COALESCE(e.emp_designation, '--') AS designation, 
            COALESCE(b.branch_name, e.current_branch_id, '--') AS branch, 
            u.last_login_on AS last_login, 
            u.role_id AS user_role, 
            u.status_type AS user_status,
            COALESCE(u.profile_image, '') AS user_photo
        FROM users u
        LEFT JOIN employees e ON u.emp_id = e.emp_id AND u.cid = e.cid
        LEFT JOIN branches b ON e.current_branch_id = b.branch_id AND e.cid = b.cid
        ORDER BY u.id DESC; 
    """  
    try:
        raw_users = db.executesql(user_records_sql, as_dict=True)
    except Exception:
        raw_users = []

    # Format last_login if datetime object to 12-hour format (AM/PM)
    for u in raw_users:
        last_login_val = u.get("last_login")
        if last_login_val:
            if isinstance(last_login_val, datetime):
                u["last_login"] = last_login_val.strftime("%Y-%m-%d %I:%M:%S %p")
            elif isinstance(last_login_val, str) and last_login_val.strip() and last_login_val != "--":
                try:
                    dt_obj = datetime.strptime(last_login_val.strip().split('.')[0], "%Y-%m-%d %H:%M:%S")
                    u["last_login"] = dt_obj.strftime("%Y-%m-%d %I:%M:%S %p")
                except Exception:
                    u["last_login"] = str(last_login_val)
            else:
                u["last_login"] = str(last_login_val)
        else:
            u["last_login"] = "--"

    keywords = request.query.get("keywords", "").strip().lower()
    role = request.query.get("role", "").strip()
    status = request.query.get("status", "").strip()
    export_format = request.query.get("export", "").strip().lower()

    # 1. Filtering Logic
    filtered_users = []
    for u in raw_users:
        u_name = str(u.get("user_name") or "").lower()
        u_email = str(u.get("user_email") or "").lower()
        u_id = str(u.get("user_id") or "").lower()
        u_dept = str(u.get("department") or "").lower()
        u_branch = str(u.get("branch") or "").lower()
        u_role = str(u.get("user_role") or "")
        u_status = str(u.get("user_status") or "")

        if keywords:
            kw_match = (
                keywords in u_name
                or keywords in u_email
                or keywords in u_id
                or keywords in u_dept
                or keywords in u_branch
            )
            if not kw_match:
                continue

        if role and u_role.lower() != role.lower():
            continue

        if status and u_status.lower() != status.lower():
            continue

        filtered_users.append(u)

    # 2. Export Handling
    if export_format in ["xlsx", "xls", "csv"]:
        filename = f"User_List_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        headers = ["ID", "Name", "Email", "Department", "Designation", "Branch", "Role", "Status", "Last Login"]

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for u in filtered_users:
                writer.writerow([
                    u.get("user_id", ""), u.get("user_name", ""), u.get("user_email", ""),
                    u.get("department", ""), u.get("designation", ""), u.get("branch", ""),
                    u.get("user_role", ""), u.get("user_status", ""), u.get("last_login", "")
                ])
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return output.getvalue()

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
            xml_data.append('<Worksheet ss:Name="Users"><Table>')
            xml_data.append('<Row ss:Height="26">')
            for h in headers:
                xml_data.append(f'  <Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{h}</Data></Cell>')
            xml_data.append('</Row>')
            for u in filtered_users:
                xml_data.append('<Row ss:Height="22">')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{u.get("user_id", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{u.get("user_name", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{u.get("user_email", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{u.get("department", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{u.get("designation", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{u.get("branch", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{u.get("user_role", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{u.get("user_status", "")}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{u.get("last_login", "")}</Data></Cell>')
                xml_data.append('</Row>')
            xml_data.append('</Table></Worksheet></Workbook>')
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
            return "\n".join(xml_data)

    # 3. Stats Calculation
    total_users = len(raw_users)
    active_users = sum(1 for u in raw_users if str(u.get("user_status", "")).upper() == "ACTIVE")
    inactive_users = sum(1 for u in raw_users if str(u.get("user_status", "")).upper() in ["INACTIVE", "LOCKED", "BLOCKED"])
    admin_users = sum(1 for u in raw_users if "admin" in str(u.get("user_role", "")).lower())

    stats = {
        "total": total_users,
        "active": active_users,
        "inactive": inactive_users,
        "admin": admin_users,
    }

    # 4. Limit and Pagination Logic
    try:
        limit = int(request.query.get("limit", 10))
    except (ValueError, TypeError):
        limit = 10
    if limit not in [10, 25, 50, 100]:
        limit = 10

    total_filtered = len(filtered_users)
    total_pages = math.ceil(total_filtered / limit) if total_filtered > 0 else 1

    try:
        page = int(request.query.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_users = filtered_users[start_idx:end_idx]

    pagination = {
        "current_page": page,
        "limit": limit,
        "page_size": limit,
        "total_pages": total_pages,
        "total_items": total_filtered,
        "start_item": start_idx + 1 if total_filtered > 0 else 0,
        "end_item": min(end_idx, total_filtered),
    }

    return dict(all_users=paginated_users, stats=stats, pagination=pagination)


@action("administration/add_user", method=["GET", "POST"])
@view_page("administration/add_user.html", title="Add New User | Administration")
@web_auth_required
def add_user():
    user_cid = session.user.get("cid", "")
    return dict(user_cid=user_cid)


@action("administration/edit_user", method=["GET", "POST"])
@action("administration/edit_user/<user_id>", method=["GET", "POST"])
@view_page("administration/edit_user.html", title="Edit User | Administration")
@web_auth_required
def edit_user(user_id=None):
    user_cid = session.user.get("cid", "")
    if user_id is None:
        user_id = request.query.get("id") or request.query.get("user_id")
    return dict(user_cid=user_cid, user_id=user_id)



