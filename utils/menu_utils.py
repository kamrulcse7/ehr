import time
import copy
from ..core.db import db

_MENU_CACHE = {}
_CACHE_TTL = 300  # 5 minutes RAM cache TTL

def clear_menu_cache():
    """Clear in-memory menu cache when permissions or modules change."""
    global _MENU_CACHE
    _MENU_CACHE = {}

def get_user_menu_tree(user):
    if not user:
        return []

    cid = user.get("cid") or ""
    role_id = user.get("user_role") or ""
    cache_key = (cid, role_id)
    now = time.time()

    if cache_key in _MENU_CACHE:
        cached_time, cached_tree = _MENU_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL:
            return copy.deepcopy(cached_tree)

    if role_id in ("SUPER_ADMIN", "SYSTEM_ADMIN"):
        if cid:
            menu_sql = """
            SELECT 
                m.module_id, 
                m.parent_module_id, 
                COALESCE(cm.custom_name, m.module_name) AS display_title, 
                COALESCE(cm.custom_icon, m.icon, 'grid_view') AS icon, 
                COALESCE(cm.custom_route_path, m.route_path, '') AS route_path, 
                m.is_clickable,
                COALESCE(NULLIF(cm.display_order, 0), m.display_order, 0) AS display_order
            FROM modules m
            LEFT JOIN company_modules cm ON m.module_id = cm.module_id AND LOWER(cm.cid) = LOWER(%s)
            WHERE m.status_type = 'ACTIVE'
              AND (cm.status_type IS NULL OR cm.status_type = 'ACTIVE')
            ORDER BY COALESCE(NULLIF(cm.display_order, 0), m.display_order) ASC, m.display_order ASC;
            """
            modules_list = db.executesql(menu_sql, placeholders=[cid], as_dict=True)
        else:
            menu_sql = """
            SELECT 
                m.module_id, 
                m.parent_module_id, 
                m.module_name AS display_title, 
                COALESCE(icon, 'grid_view') AS icon, 
                COALESCE(route_path, '') AS route_path, 
                is_clickable,
                display_order
            FROM modules m
            WHERE m.status_type = 'ACTIVE'
            ORDER BY m.display_order ASC;
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
            m.is_clickable,
            COALESCE(NULLIF(cm.display_order, 0), m.display_order, 0) AS display_order
        FROM role_module_permissions rmp
        JOIN modules m ON rmp.module_id = m.module_id
        LEFT JOIN company_modules cm ON m.module_id = cm.module_id AND LOWER(cm.cid) = LOWER(%s)
        WHERE rmp.role_id = %s
          AND rmp.can_view = 1
          AND m.status_type = 'ACTIVE'
          AND (cm.status_type IS NULL OR cm.status_type = 'ACTIVE')
        ORDER BY COALESCE(NULLIF(cm.display_order, 0), m.display_order) ASC, m.display_order ASC;
        """
        modules_list = db.executesql(menu_sql, placeholders=[cid, role_id], as_dict=True)

    # Convert flat list into Parent-Child Menu Tree
    parent_map = {}
    for item in modules_list:
        item["children"] = []
        parent_map[item["module_id"]] = item

    # Auto-resolve parent modules if child modules are allowed but parent header is omitted from role permissions / company modules
    missing_p_ids = {
        item["parent_module_id"] 
        for item in modules_list 
        if item.get("parent_module_id") and item["parent_module_id"] not in parent_map
    }

    if missing_p_ids:
        in_clause = ",".join(["%s"] * len(missing_p_ids))
        if cid:
            parent_sql = f"""
            SELECT 
                m.module_id, 
                m.parent_module_id, 
                COALESCE(cm.custom_name, m.module_name) AS display_title, 
                COALESCE(cm.custom_icon, m.icon, 'folder') AS icon, 
                COALESCE(cm.custom_route_path, m.route_path, '') AS route_path, 
                m.is_clickable,
                COALESCE(NULLIF(cm.display_order, 0), m.display_order, 0) AS display_order
            FROM modules m
            LEFT JOIN company_modules cm ON m.module_id = cm.module_id AND LOWER(cm.cid) = LOWER(%s)
            WHERE m.module_id IN ({in_clause}) AND m.status_type = 'ACTIVE'
            ORDER BY COALESCE(NULLIF(cm.display_order, 0), m.display_order) ASC, m.display_order ASC;
            """
            parent_modules = db.executesql(parent_sql, placeholders=[cid] + list(missing_p_ids), as_dict=True)
        else:
            parent_sql = f"""
            SELECT 
                m.module_id, 
                m.parent_module_id, 
                m.module_name AS display_title, 
                COALESCE(m.icon, 'folder') AS icon, 
                COALESCE(m.route_path, '') AS route_path, 
                m.is_clickable,
                m.display_order
            FROM modules m
            WHERE m.module_id IN ({in_clause}) AND m.status_type = 'ACTIVE'
            ORDER BY m.display_order ASC;
            """
            parent_modules = db.executesql(parent_sql, placeholders=list(missing_p_ids), as_dict=True)

        for p_item in parent_modules:
            p_item["children"] = []
            parent_map[p_item["module_id"]] = p_item

    # Build final hierarchy
    parents = []
    parent_ids_added = set()

    for item in list(parent_map.values()):
        p_id = item.get("parent_module_id")
        if not p_id and item["module_id"] not in parent_ids_added:
            parents.append(item)
            parent_ids_added.add(item["module_id"])

    for item in modules_list:
        p_id = item.get("parent_module_id")
        if p_id and p_id in parent_map:
            if not any(c["module_id"] == item["module_id"] for c in parent_map[p_id]["children"]):
                parent_map[p_id]["children"].append(item)
        elif p_id and p_id not in parent_map:
            if item["module_id"] not in parent_ids_added:
                parents.append(item)
                parent_ids_added.add(item["module_id"])

    # Sort root modules and submodules by display_order
    parents.sort(key=lambda x: int(x.get("display_order") or 0))
    for p in parents:
        if p.get("children"):
            p["children"].sort(key=lambda x: int(x.get("display_order") or 0))

    final_tree = [p for p in parents if p.get("children") or p.get("is_clickable")]

    _MENU_CACHE[cache_key] = (now, copy.deepcopy(final_tree))
    return final_tree


def get_active_module_info(user_menu, current_path):
    if not user_menu or not current_path:
        return {"parent_title": None, "child_title": None}

    clean_path = str(current_path).strip().lower().strip('/')
    
    # 1. Direct Keyword Mappings for Sub-actions
    if any(kw in clean_path for kw in ('transfer', 'posting')):
        for parent in user_menu:
            for child in parent.get('children', []):
                c_route = str(child.get('route_path') or '').lower()
                c_title = str(child.get('display_title') or '').lower()
                if 'transfer' in c_route or 'posting' in c_route or 'transfer' in c_title or 'posting' in c_title:
                    return {"parent_title": parent.get('display_title'), "child_title": child.get('display_title')}

    if any(kw in clean_path for kw in ('directory', 'employee')):
        for parent in user_menu:
            for child in parent.get('children', []):
                c_route = str(child.get('route_path') or '').lower()
                c_title = str(child.get('display_title') or '').lower()
                if 'directory' in c_route or 'directory' in c_title:
                    return {"parent_title": parent.get('display_title'), "child_title": child.get('display_title')}

    # 2. General Token Matching
    path_segments = [s for s in clean_path.split('/') if s and not s.isdigit()]
    target_action = path_segments[-1] if path_segments else ""

    best_match = None
    best_score = 0

    for parent in user_menu:
        parent_title = parent.get('display_title')
        
        for child in parent.get('children', []):
            child_title = child.get('display_title')
            child_route = str(child.get('route_path') or '').strip().lower().strip('/')
            module_id = str(child.get('module_id') or '').lower()
            
            if not child_route and not module_id:
                continue

            child_segments = [s for s in child_route.split('/') if s]
            last_child_seg = child_segments[-1] if child_segments else ""

            score = 0

            # Exact route match
            if child_route and (child_route == clean_path or clean_path.endswith(child_route)):
                score = 100
            # Action exact match
            elif last_child_seg and last_child_seg == target_action:
                score = 85
            else:
                action_tokens = [t for t in target_action.split('_') if len(t) > 3]
                route_tokens = [t for t in last_child_seg.split('_') if len(t) > 3]
                module_tokens = [t for t in module_id.split('_') if len(t) > 3]

                all_child_tokens = set(route_tokens + module_tokens)
                
                matched_token = False
                for act_tok in action_tokens:
                    for ch_tok in all_child_tokens:
                        if act_tok in ch_tok or ch_tok in act_tok:
                            if act_tok not in ('employee', 'employees', 'report', 'reports', 'manage'):
                                matched_token = True
                                break
                    if matched_token:
                        break

                if matched_token:
                    score = 70

            if score > best_score:
                best_score = score
                best_match = {
                    "parent_title": parent_title,
                    "child_title": child_title
                }

    if best_match and best_score > 0:
        return best_match

    # Fallback to parent match
    for parent in user_menu:
        parent_route = str(parent.get('route_path') or '').strip().lower().strip('/')
        if parent_route and parent_route in clean_path:
            return {"parent_title": parent.get('display_title'), "child_title": None}

    return {"parent_title": None, "child_title": None}

