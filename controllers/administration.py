from py4web import URL, action, redirect, request
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page


@action("administration/role_management")
@view_page("administration/role_management.html")
@web_auth_required
def role_management():
    roles = [
        {"id": 1, "name": "Super Admin", "description": "Full system access"},
        {
            "id": 2,
            "name": "HR Officer",
            "description": "Staff & records management",
        },
        {"id": 3, "name": "Branch Manager", "description": "Regional oversight"},
        {"id": 4, "name": "Report Viewer", "description": "Read-only analytics"},
    ]

    # Grouped modules according to your sidebar navigation structure
    permission_groups = [
        {
            "group_name": "Administration",
            "modules": [
                {
                    "id": "user_mgmt",
                    "name": "User Management",
                    "icon": "manage_accounts",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
                {
                    "id": "role_mgmt",
                    "name": "Role Management",
                    "icon": "admin_panel_settings",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                        "approve": True,
                    },
                    "disabled_actions": [],
                },
            ],
        },
        {
            "group_name": "Employees",
            "modules": [
                {
                    "id": "emp_mgmt",
                    "name": "Employees Management",
                    "icon": "badge",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
                {
                    "id": "transfer_mgmt",
                    "name": "Transfer Management",
                    "icon": "swap_horiz",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                        "approve": True,
                    },
                    "disabled_actions": [],
                },
            ],
        },
        {
            "group_name": "Organization",
            "modules": [
                {
                    "id": "departments",
                    "name": "Departments",
                    "icon": "account_tree",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
                {
                    "id": "designations",
                    "name": "Designations",
                    "icon": "workspace_premium",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
                {
                    "id": "branches",
                    "name": "Branches",
                    "icon": "store",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
            ],
        },
        {
            "group_name": "Analytics & System",
            "modules": [
                {
                    "id": "reports",
                    "name": "Reports",
                    "icon": "bar_chart",
                    "perms": {"view": True, "export": True},
                    "disabled_actions": ["create", "edit", "delete", "approve"],
                },
                {
                    "id": "settings",
                    "name": "Settings",
                    "icon": "settings",
                    "perms": {
                        "view": True,
                        "create": True,
                        "edit": True,
                        "delete": True,
                        "export": True,
                    },
                    "disabled_actions": ["approve"],
                },
            ],
        },
    ]

    return dict(roles=roles, permission_groups=permission_groups)


@action("administration/create_role")
@view_page("administration/create_role.html")
@web_auth_required
def create_role():
    return dict()