from py4web import URL, action, redirect, request
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page

roles = [
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
    

@action("administration/role_management")
@view_page("administration/role_management.html")
@web_auth_required
def role_management():
    return dict(roles=roles)



@action("administration/role_form")
@view_page("administration/role_form.html")
@web_auth_required
def role_form():
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
            (r for r in roles if str(r["role_id"]) == str(role_id)), None
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