from ..core.db import db

DEFAULT_FULL_PERMISSIONS = {
    "can_view": True,
    "can_add": True,
    "can_edit": True,
    "can_delete": True,
    "can_export": True,
    "can_import": True,
    "can_print": True,
    "can_approve": True,
    "can_reject": True,
    "can_upload": True,
    "can_download": True,
}

DEFAULT_NO_PERMISSIONS = {
    "can_view": False,
    "can_add": False,
    "can_edit": False,
    "can_delete": False,
    "can_export": False,
    "can_import": False,
    "can_print": False,
    "can_approve": False,
    "can_reject": False,
    "can_upload": False,
    "can_download": False,
}

MODULE_ROUTE_MAP = [
    # (route_prefix_or_keyword, module_id)
    ("dashboard", "DASHBOARD"),
    
    ("employees/employee_directory", "EMPLOYEE_DIR"),
    ("employees/show_directory", "EMPLOYEE_DIR"),
    ("employees/directory_manage", "EMPLOYEE_DIR"),
    ("employees/add_directory", "EMPLOYEE_DIR"),
    ("employees/edit_directory", "EMPLOYEE_DIR"),
    ("employees/import_directory", "EMPLOYEE_DIR"),

    ("employees/postings_transfers", "POSTING_TRANS"),
    ("employees/show_transfer", "POSTING_TRANS"),
    ("employees/transfer_manage", "POSTING_TRANS"),
    ("employees/delete_transfer", "POSTING_TRANS"),
    ("employees/import_transfer", "POSTING_TRANS"),

    ("administration/companies", "COMPANY_MGMT"),
    ("administration/company_view", "COMPANY_MGMT"),
    ("administration/add_company", "COMPANY_MGMT"),
    ("administration/edit_company", "COMPANY_MGMT"),
    ("administration/company_manage", "COMPANY_MGMT"),
    ("administration/import_companies", "COMPANY_MGMT"),

    ("administration/roles_permissions", "ROLES_PERM"),
    ("administration/role_manage", "ROLES_PERM"),

    ("administration/users", "USER_MGMT"),
    ("administration/user_view", "USER_MGMT"),
    ("administration/add_user", "USER_MGMT"),
    ("administration/edit_user", "USER_MGMT"),
    ("administration/user_manage", "USER_MGMT"),
    ("administration/import_users", "USER_MGMT"),

    ("administration/audit_logs", "AUDIT_LOGS"),

    ("reports/employee_reports", "EMP_REPORTS"),
    ("reports/transfer_logs", "TRANSFER_LOGS"),
    ("reports/custom_reports", "CUSTOM_REPORTS"),
]


def resolve_module_id(path):
    """
    Resolves an HTTP request URL path to its corresponding module_id.
    """
    if not path:
        return None

    clean_path = str(path).strip().lower().strip('/')
    parts = [p for p in clean_path.split('/') if p]

    candidate_paths = [
        "/".join(parts),
        "/".join(parts[1:]) if len(parts) > 1 else ""
    ]

    for candidate in candidate_paths:
        if not candidate:
            continue
        for route, module_id in MODULE_ROUTE_MAP:
            clean_route = route.strip().lower().strip('/')
            if candidate == clean_route or candidate.startswith(clean_route + '/'):
                return module_id

    return None


def get_user_permissions(user, module_id):
    """
    Fetches permissions dict for a given user and module_id.
    """
    if not user:
        return dict(DEFAULT_NO_PERMISSIONS)

    if not module_id:
        return dict(DEFAULT_NO_PERMISSIONS)

    role_id = (user.get("user_role") or "").strip().upper()

    # Root / Super Admin / System Admin full bypass
    if role_id in ("SUPER_ADMIN", "SYSTEM_ADMIN", "ROOT"):
        return dict(DEFAULT_FULL_PERMISSIONS)

    if module_id == "DASHBOARD":
        dash_perms = dict(DEFAULT_NO_PERMISSIONS)
        dash_perms["can_view"] = True
        return dash_perms

    cid = user.get("cid", "")

    # Query role_module_permissions for role_id & module_id
    perm_sql = """
    SELECT 
        can_view, can_add, can_edit, can_delete, can_export, can_import,
        can_print, can_approve, can_reject, can_upload, can_download
    FROM role_module_permissions
    WHERE UPPER(role_id) = %s AND UPPER(module_id) = %s
    LIMIT 1;
    """
    res = db.executesql(perm_sql, placeholders=[role_id, module_id.upper()], as_dict=True)

    if not res:
        return dict(DEFAULT_NO_PERMISSIONS)

    p = res[0]
    return {
        "can_view": bool(p.get("can_view")),
        "can_add": bool(p.get("can_add")),
        "can_edit": bool(p.get("can_edit")),
        "can_delete": bool(p.get("can_delete")),
        "can_export": bool(p.get("can_export")),
        "can_import": bool(p.get("can_import")),
        "can_print": bool(p.get("can_print")),
        "can_approve": bool(p.get("can_approve")),
        "can_reject": bool(p.get("can_reject")),
        "can_upload": bool(p.get("can_upload")),
        "can_download": bool(p.get("can_download")),
    }
