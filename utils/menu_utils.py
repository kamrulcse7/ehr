from ..core.db import db

def get_user_menu_tree(user):
    if not user:
        return []

    cid = user.get("cid")
    role_id = user.get("user_role")

    if role_id in ("SUPER_ADMIN", "SYSTEM_ADMIN"):
        menu_sql = """
        SELECT 
            module_id, 
            module_name AS display_title, 
            parent_module_id, 
            COALESCE(icon, 'grid_view') AS icon, 
            COALESCE(route_path, '') AS route_path, 
            is_clickable
        FROM modules
        WHERE status_type = 'ACTIVE'
        ORDER BY display_order ASC;
        """
        modules_list = db.executesql(menu_sql, as_dict=True)
    else:
        menu_sql = """
        SELECT 
            m.module_id,
            m.parent_module_id,
            COALESCE(cm.custom_name, m.module_name) AS display_title,
            COALESCE(cm.custom_icon, m.icon, 'folder') AS icon,
            COALESCE(cm.custom_route_path, m.route_path, '') AS route_path,
            m.is_clickable
        FROM company_modules cm
        JOIN modules m ON cm.module_id = m.module_id
        JOIN role_module_permissions rmp ON m.module_id = rmp.module_id
        WHERE cm.cid = %s
          AND rmp.role_id = %s
          AND cm.status_type = 'ACTIVE'
          AND rmp.can_view = 1
          AND m.status_type = 'ACTIVE'
        ORDER BY COALESCE(cm.display_order, m.display_order) ASC;
        """
        modules_list = db.executesql(menu_sql, placeholders=[cid, role_id], as_dict=True)

    # Convert flat list into Parent-Child Menu Tree
    parent_map = {}
    parents = []

    for item in modules_list:
        item["children"] = []
        parent_map[item["module_id"]] = item

    for item in modules_list:
        p_id = item.get("parent_module_id")
        if p_id and p_id in parent_map:
            parent_map[p_id]["children"].append(item)
        elif not p_id:
            parents.append(item)

    return parents
