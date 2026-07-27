from py4web import URL, action, redirect, request
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page
import math

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
    

@action("administration/roles")
@view_page("administration/roles.html")
@web_auth_required
def roles():
    return dict(all_roles=all_roles)



@action("administration/role_manage")
@view_page("administration/role_manage.html")
@web_auth_required
def role_manage():
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
@view_page("administration/users.html")
@web_auth_required
def users():
    raw_users = [
        {
            "user_id": "1",
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "department": "Human Resources",
            "designation": "Manager",
            "branch": "Dhaka",
            "last_login": "2022-01-01 12:00:00",
            "user_role": "Admin",
            "user_status": "Active",
        },
        {
            "user_id": "2",
            "user_name": "Jane Doe",
            "user_email": "jane@example.com",
            "department": "Human Resources",
            "designation": "Manager",
            "branch": "Dhaka",
            "last_login": "2022-01-01 12:00:00",
            "user_role": "Admin",
            "user_status": "Active",
        },
        {
            "user_id": "3",
            "user_name": "Rahim Ahmed",
            "user_email": "rahim@example.com",
            "department": "IT",
            "designation": "Developer",
            "branch": "Dhaka",
            "last_login": "2022-01-02 10:30:00",
            "user_role": "User",
            "user_status": "Active",
        },
        {
            "user_id": "4",
            "user_name": "Karim Uddin",
            "user_email": "karim@example.com",
            "department": "Finance",
            "designation": "Accountant",
            "branch": "Chittagong",
            "last_login": "2022-01-03 15:20:00",
            "user_role": "User",
            "user_status": "Inactive",
        },
        {
            "user_id": "5",
            "user_name": "Sultana Razia",
            "user_email": "sultana@example.com",
            "department": "Operations",
            "designation": "Executive",
            "branch": "Sylhet",
            "last_login": "2022-01-04 09:15:00",
            "user_role": "Manager",
            "user_status": "Active",
        },
        {
            "user_id": "6",
            "user_name": "Tanvir Hasan",
            "user_email": "tanvir@example.com",
            "department": "IT",
            "designation": "SysAdmin",
            "branch": "Dhaka",
            "last_login": "2022-01-05 18:00:00",
            "user_role": "Admin",
            "user_status": "Locked",
        },
    
    ]

    # --- ১. Stats Calculation (Controller Side) ---
    total_users = len(raw_users)
    active_users = sum(1 for u in raw_users if u.get("user_status") == "Active")
    inactive_users = sum(
        1 for u in raw_users if u.get("user_status") in ["Inactive", "Locked"]
    )
    admin_users = sum(1 for u in raw_users if u.get("user_role") == "Admin")

    stats = {
        "total": total_users,
        "active": active_users,
        "inactive": inactive_users,
        "admin": admin_users,
    }

    # --- ২. Pagination Logic ---
    try:
        page = int(request.query.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    page_size = 5 
    total_pages = math.ceil(total_users / page_size) if total_users > 0 else 1

    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages

    # Slice index calculation
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_users = raw_users[start_idx:end_idx]

    pagination = {
        "current_page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_items": total_users,
        "start_item": start_idx + 1 if total_users > 0 else 0,
        "end_item": min(end_idx, total_users),
    }

    return dict(all_users=paginated_users, stats=stats, pagination=pagination)


@action("administration/user_manage")
@view_page("administration/user_manage.html")
@web_auth_required
def user_manage():
    return dict()



