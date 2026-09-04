import time
from ..core.db import db

_ROUTE_CACHE = {}
_PERM_CACHE = {}
_CACHE_TTL = 300  # 5 minutes RAM cache TTL

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


def clear_permission_cache():
    """
    Clears RAM cache for permissions and routes. Also invalidates menu cache.
    Call this whenever roles or role_module_permissions are updated.
    """
    global _PERM_CACHE, _ROUTE_CACHE
    _PERM_CACHE = {}
    _ROUTE_CACHE = {}
    try:
        from .menu_utils import clear_menu_cache
        clear_menu_cache()
    except Exception:
        pass


def get_db_route_map(cid=None):
    """
    Fetches active module route mappings directly from the database.
    Caches the results in RAM for high performance.
    """
    now = time.time()
    cache_key = (cid or "").upper()

    if cache_key in _ROUTE_CACHE:
        cached_time, cached_routes = _ROUTE_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL:
            return cached_routes

    if cid:
        sql = """
        SELECT 
            m.module_id,
            COALESCE(cm.custom_route_path, m.route_path) AS route_path
        FROM modules m
        LEFT JOIN company_modules cm ON m.module_id = cm.module_id AND LOWER(cm.cid) = LOWER(%s)
        WHERE m.status_type = 'ACTIVE' 
          AND (cm.status_type IS NULL OR cm.status_type = 'ACTIVE')
          AND COALESCE(cm.custom_route_path, m.route_path) IS NOT NULL;
        """
        rows = db.executesql(sql, placeholders=[cid], as_dict=True)
    else:
        sql = """
        SELECT module_id, route_path 
        FROM modules 
        WHERE status_type = 'ACTIVE' AND route_path IS NOT NULL AND route_path != '';
        """
        rows = db.executesql(sql, as_dict=True)

    route_list = []
    for r in rows:
        r_path = (r.get("route_path") or "").strip().lower().strip('/')
        mod_id = (r.get("module_id") or "").strip().upper()
        if r_path and mod_id:
            route_list.append((r_path, mod_id))

    _ROUTE_CACHE[cache_key] = (now, route_list)
    return route_list


def resolve_module_id(path, cid=None):
    """
    Dynamically resolves an HTTP request URL path to its corresponding module_id
    by checking database-registered module routes.
    Handles py4web app name prefixes e.g. /ehr/employees/employee_directory.
    """
    if not path:
        return None

    clean_path = str(path).strip().lower().strip('/')
    if not clean_path:
        return "DASHBOARD"

    parts = [p for p in clean_path.split('/') if p]
    if not parts:
        return None

    # Candidate paths: try full path (e.g. "ehr/employees/directory") and stripped app path (e.g. "employees/directory")
    candidate_paths = [clean_path]
    if len(parts) > 1:
        candidate_paths.append("/".join(parts[1:]))

    for cand in candidate_paths:
        if cand in ('index', 'home', 'dashboard', 'dashboard/index'):
            return "DASHBOARD"

    routes = get_db_route_map(cid)

    # 1. Direct exact match or URL prefix match against registered DB routes
    for cand in candidate_paths:
        for route_path, mod_id in routes:
            if cand == route_path or cand.startswith(route_path + '/'):
                return mod_id

    # 2. Extract controller and action segments for sub-action keyword resolution
    for cand in candidate_paths:
        cand_parts = [p for p in cand.split('/') if p]
        if not cand_parts:
            continue

        controller = cand_parts[0]
        action = cand_parts[1] if len(cand_parts) > 1 else ""

        best_mod = None
        best_score = 0

        for route_path, mod_id in routes:
            r_parts = [p for p in route_path.split('/') if p]
            if not r_parts:
                continue
            r_controller = r_parts[0]
            r_action = r_parts[1] if len(r_parts) > 1 else ""

            if controller != r_controller:
                continue

            score = 10
            action_tokens = set([t for t in action.replace('_', ' ').split() if len(t) > 2])
            route_tokens = set([t for t in r_action.replace('_', ' ').split() if len(t) > 2])
            mod_tokens = set([t for t in mod_id.lower().replace('_', ' ').split() if len(t) > 2])

            overlap = action_tokens.intersection(route_tokens | mod_tokens)
            if overlap:
                score += 50 + len(overlap) * 10

            for act_t in action_tokens:
                for r_t in (route_tokens | mod_tokens):
                    if act_t in r_t or r_t in act_t:
                        score += 25

            if score > best_score:
                best_score = score
                best_mod = mod_id

        if best_mod and best_score >= 35:
            return best_mod

    return None


def get_user_permissions(user, module_id):
    """
    Fetches permissions dict for a given user and module_id.
    Uses RAM caching to eliminate redundant database hits on every request.
    """
    if not user:
        return dict(DEFAULT_NO_PERMISSIONS)

    role_id = (user.get("user_role") or user.get("role_id") or "").strip().upper()

    # Root / Super Admin / System Admin ALWAYS get full access
    if role_id in ("SUPER_ADMIN", "SYSTEM_ADMIN", "ROOT"):
        return dict(DEFAULT_FULL_PERMISSIONS)

    if not module_id:
        return dict(DEFAULT_NO_PERMISSIONS)

    if module_id.upper() == "DASHBOARD":
        dash_perms = dict(DEFAULT_NO_PERMISSIONS)
        dash_perms["can_view"] = True
        return dash_perms

    cache_key = (role_id, module_id.upper())
    now = time.time()

    if cache_key in _PERM_CACHE:
        cached_time, cached_perms = _PERM_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL:
            return dict(cached_perms)

    # Query DB for permissions
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
        perms = dict(DEFAULT_NO_PERMISSIONS)
    else:
        p = res[0]
        perms = {
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

    _PERM_CACHE[cache_key] = (now, perms)
    return dict(perms)

