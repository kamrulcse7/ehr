from py4web import URL, action, redirect, request, response
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page
from ..core.db import db_datetime
import math
import io
import csv
import os
import time
from datetime import datetime


def _save_company_branding_file(file_obj, prefix, cid_val, max_bytes=120 * 1024):
    if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
        UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "company")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file_obj.filename)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico", ".svg"]:
            content = file_obj.file.read()
            if len(content) > max_bytes:
                flash.set("Company Logo file size exceeds 120KB limit.", "danger")
                return None
            base_prefix = f"{cid_val.lower()}_{prefix}"
            for f in os.listdir(UPLOAD_DIR):
                if f.startswith(base_prefix + "."):
                    try:
                        os.remove(os.path.join(UPLOAD_DIR, f))
                    except Exception:
                        pass
            saved_filename = f"{base_prefix}{ext}"
            saved_file_path = os.path.join(UPLOAD_DIR, saved_filename)
            with open(saved_file_path, "wb") as f:
                f.write(content)
            return URL(f"static/uploads/company/{saved_filename}")
    return None


def _delete_company_branding_file(file_url):
    if not file_url:
        return
    if file_url.startswith("http://") or file_url.startswith("https://"):
        return
    filename = os.path.basename(file_url)
    if filename:
        UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "company")
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


def _save_user_avatar_file(file_obj, user_id_val, max_bytes=120 * 1024):
    if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
        UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "user_photos")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file_obj.filename)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            content = file_obj.file.read()
            if len(content) > max_bytes:
                flash.set("User avatar file size exceeds 120KB limit.", "danger")
                return None
            clean_uid = "".join(c for c in str(user_id_val).lower() if c.isalnum() or c in ("-", "_"))
            base_prefix = f"user_{clean_uid}"
            for f in os.listdir(UPLOAD_DIR):
                if f.startswith(base_prefix + "."):
                    try:
                        os.remove(os.path.join(UPLOAD_DIR, f))
                    except Exception:
                        pass
            saved_filename = f"{base_prefix}_{int(time.time())}{ext}"
            saved_file_path = os.path.join(UPLOAD_DIR, saved_filename)
            with open(saved_file_path, "wb") as f:
                f.write(content)
            return URL(f"static/uploads/user_photos/{saved_filename}")
    return None


@action("administration/companies", method=["GET", "POST"])
@view_page("administration/companies.html", title="Company Management | Administration")
@web_auth_required
def companies():
    action_type = (request.query.get("action") or "").strip()
    delete_id = request.query.get("id") or request.query.get("delete_id")

    if action_type == "delete" and delete_id:
        try:
            del_id = int(delete_id)
            comp_rows = db.executesql("SELECT cid, company_name FROM companies WHERE id = %s LIMIT 1", [del_id], as_dict=True)
            if comp_rows:
                comp = comp_rows[0]
                cid = comp["cid"]
                name = comp["company_name"]
                updated_by = session.user.get("username") or session.user.get("user_id") or "SYSTEM"
                db.executesql(
                    "UPDATE companies SET status_type = 'DELETED', updated_on = NOW(), updated_by = %s WHERE id = %s",
                    [updated_by, del_id]
                )
                flash.set(f"Company '{name}' ({cid}) status updated to DELETED.", "success")
            else:
                flash.set("Company record not found.", "danger")
        except Exception as e:
            flash.set(f"Failed to delete company: {str(e)}", "danger")
        redirect(URL("administration/companies"))

    # 1. Fetch Summary Stats (excluding soft-deleted)
    stats_sql = """
    SELECT 
        COUNT(CASE WHEN status_type != 'DELETED' THEN 1 END) AS total,
        SUM(CASE WHEN status_type = 'ACTIVE' THEN 1 ELSE 0 END) AS active,
        SUM(CASE WHEN status_type = 'INACTIVE' THEN 1 ELSE 0 END) AS inactive
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
    else:
        where_clauses.append("status_type != 'DELETED'")

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
        limit = max(1, int(request.query.get("limit", 10)))
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
        companies=paginated_companies,
        stats=stats,
        pagination=pagination,
    )

@action("administration/company_manage/<company_id:int>", method=["GET", "POST"])
@action("administration/company_manage", method=["GET", "POST"])
@action("administration/add_company", method=["GET", "POST"])
@action("administration/edit_company/<company_id:int>", method=["GET", "POST"])
@action("administration/edit_company", method=["GET", "POST"])
@view_page("administration/company_manage.html", title="Company Management | Administration")
@web_auth_required
def company_manage(company_id=None):
    if company_id is None:
        company_id = request.query.get("id") or request.query.get("company_id")

    company = None
    if company_id:
        comp_rows = db.executesql("SELECT * FROM companies WHERE id = %s LIMIT 1", [company_id], as_dict=True)
        if not comp_rows:
            flash.set("Company record not found.", "danger")
            redirect(URL("administration/companies"))
        company = comp_rows[0]

    form_data = dict(company) if company else {}

    if request.method == "POST":
        form_data = dict(request.forms)
        def clean_val(val):
            val = str(val).strip() if val else None
            return val if val != "" else None

        company_name = clean_val(request.forms.get("company_name"))
        legal_name = clean_val(request.forms.get("legal_name"))
        email = clean_val(request.forms.get("email"))
        phone = clean_val(request.forms.get("phone"))
        website = clean_val(request.forms.get("website"))
        address_line1 = clean_val(request.forms.get("address_line1"))
        address_line2 = clean_val(request.forms.get("address_line2"))
        city = clean_val(request.forms.get("city"))
        state = clean_val(request.forms.get("state"))
        country = clean_val(request.forms.get("country")) or "Bangladesh"
        postal_code = clean_val(request.forms.get("postal_code"))
        timezone = clean_val(request.forms.get("timezone")) or "UTC+06:00"
        language_code = clean_val(request.forms.get("language_code")) or (company.get("language_code") if company else "en") or "en"
        
        try:
            fiscal_year_start_month = int(request.forms.get("fiscal_year_start_month") or 1)
        except (ValueError, TypeError):
            fiscal_year_start_month = 1

        status_type = clean_val(request.forms.get("status_type")) or "ACTIVE"
        note = clean_val(request.forms.get("note"))

        if company:
            # Edit existing company
            if not company_name:
                flash.set("Company Name is required.", "danger")
                return dict(company=company, form_data=form_data)

            cid = company.get("cid", "comp")
            logo_file = request.files.get("logo_file")
            remove_logo = request.forms.get("remove_logo") == "1"
            old_logo_url = company.get("logo_url")

            uploaded_logo = _save_company_branding_file(logo_file, "logo", cid)

            if uploaded_logo:
                logo_url = uploaded_logo
                if old_logo_url and old_logo_url != uploaded_logo:
                    _delete_company_branding_file(old_logo_url)
            elif remove_logo:
                logo_url = None
                if old_logo_url:
                    _delete_company_branding_file(old_logo_url)
            else:
                logo_url = old_logo_url

            favicon_url = company.get("favicon_url")
            banner_url = company.get("banner_url")

            try:
                update_sql = """
                UPDATE companies SET
                    company_name = %s, legal_name = %s, email = %s, phone = %s, website = %s,
                    address_line1 = %s, address_line2 = %s, city = %s, state = %s, country = %s, postal_code = %s,
                    timezone = %s, language_code = %s, fiscal_year_start_month = %s,
                    favicon_url = %s, logo_url = %s, banner_url = %s, status_type = %s, note = %s,
                    updated_on = NOW(), updated_by = %s
                WHERE id = %s
                """
                updated_by = session.user.get("username") or session.user.get("user_id") or "SYSTEM"
                db.executesql(update_sql, [
                    company_name, legal_name, email, phone, website,
                    address_line1, address_line2, city, state, country, postal_code,
                    timezone, language_code, fiscal_year_start_month,
                    favicon_url, logo_url, banner_url, status_type, note,
                    updated_by, company_id
                ])
                flash.set(f"Company '{company_name}' updated successfully!", "success")
                redirect(URL("administration/companies"))
            except Exception as e:
                flash.set(f"Database error updating company: {str(e)}", "danger")
                return dict(company=company, form_data=form_data)
        else:
            # Add new company
            cid = clean_val(request.forms.get("cid"))
            if not cid:
                flash.set("Company ID (CID) is required.", "danger")
                return dict(company=None, form_data=form_data)

            if not company_name:
                flash.set("Company Name is required.", "danger")
                return dict(company=None, form_data=form_data)

            comp_check = db.executesql("SELECT id FROM companies WHERE LOWER(cid) = LOWER(%s) LIMIT 1", [cid])
            if comp_check:
                flash.set(f"Company ID '{cid}' already exists.", "danger")
                return dict(company=None, form_data=form_data)

            logo_file = request.files.get("logo_file")
            logo_url = _save_company_branding_file(logo_file, "logo", cid)
            favicon_url = None
            banner_url = None

            try:
                insert_sql = """
                INSERT INTO companies (
                    cid, company_name, legal_name, email, phone, website,
                    address_line1, address_line2, city, state, country, postal_code,
                    timezone, language_code, fiscal_year_start_month,
                    favicon_url, logo_url, banner_url, status_type, note,
                    created_on, created_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    NOW(), %s
                )
                """
                created_by = session.user.get("username") or session.user.get("user_id") or "SYSTEM"
                db.executesql(insert_sql, [
                    cid.upper(), company_name, legal_name, email, phone, website,
                    address_line1, address_line2, city, state, country, postal_code,
                    timezone, language_code, fiscal_year_start_month,
                    favicon_url, logo_url, banner_url, status_type, note,
                    created_by
                ])
                flash.set(f"Company '{company_name}' ({cid.upper()}) added successfully!", "success")
                redirect(URL("administration/companies"))
            except Exception as e:
                flash.set(f"Database error adding company: {str(e)}", "danger")
                return dict(company=None, form_data=form_data)

    return dict(company=company, form_data=form_data)

@action("administration/company_view/<company_id:int>")
@action("administration/company_view")
@view_page("administration/company_view.html", title="Company Details | Administration")
@web_auth_required
def company_view(company_id=None):
    if company_id is None:
        company_id = request.query.get("id") or request.query.get("company_id")

    if not company_id:
        flash.set("No company specified.", "danger")
        redirect(URL("administration/companies"))

    comp_rows = db.executesql("SELECT * FROM companies WHERE id = %s LIMIT 1", [company_id], as_dict=True)
    if not comp_rows:
        flash.set("Company record not found.", "danger")
        redirect(URL("administration/companies"))

    return dict(company=comp_rows[0])

@action("administration/import_companies", method=["GET", "POST"])
@view_page("administration/import_companies.html", title="Import Companies | Administration")
@web_auth_required
def import_companies():

    # Template download handler
    if request.query.get("template") == "csv":
        headers = [
            "Company ID (CID)", "Company Name", "Legal Name", "Email", "Phone", "Website",
            "Address Line 1", "Address Line 2", "City", "State", "Country", "Postal Code",
            "Timezone", "Fiscal Year Start Month", "Status", "Note"
        ]
        example = [
            "EON", "Eon Systems", "Eon Systems Limited", "info@eonsystems.com", "+8801700000000", "https://eonsystems.com",
            "House 12, Road 5", "Dhanmondi", "Dhaka", "Dhaka", "Bangladesh", "1205",
            "UTC+06:00", "1", "ACTIVE", "Headquarters office"
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example)

        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename="Companies_Import_Template.csv"'
        return output.getvalue()

    stats = None
    active_tab = "file"

    if request.method == "POST":
        csv_file = request.files.get("csv_file")
        csv_text = request.forms.get("csv_text")

        content = None
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

        if not content:
            flash.set("Please upload a CSV file or paste CSV text.", "danger")
            return dict(stats=None, active_tab=active_tab)

        # Parse CSV
        try:
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
        except Exception as e:
            flash.set(f"Invalid CSV structure: {str(e)}", "danger")
            return dict(stats=None, active_tab=active_tab)

        if not rows:
            flash.set("The provided CSV file is empty.", "danger")
            return dict(stats=None, active_tab=active_tab)

        # Header mapping
        raw_headers = [h.strip().lower() for h in rows[0]]
        data_rows = rows[1:]

        def get_header_idx(*names):
            for name in names:
                name_clean = name.lower()
                for idx, h in enumerate(raw_headers):
                    if h == name_clean or name_clean in h:
                        return idx
            return -1

        idx_cid = get_header_idx("company id (cid)", "cid", "company id", "company_id")
        idx_name = get_header_idx("company name", "company_name", "name")
        idx_legal = get_header_idx("legal name", "legal_name")
        idx_email = get_header_idx("email", "contact email")
        idx_phone = get_header_idx("phone", "phone number")
        idx_website = get_header_idx("website")
        idx_addr1 = get_header_idx("address line 1", "address_line1", "address line1")
        idx_addr2 = get_header_idx("address line 2", "address_line2", "address line2")
        idx_city = get_header_idx("city")
        idx_state = get_header_idx("state", "division")
        idx_country = get_header_idx("country")
        idx_postal = get_header_idx("postal code", "postal_code", "zip")
        idx_tz = get_header_idx("timezone")
        idx_lang = get_header_idx("language code", "language_code", "language")
        idx_fiscal = get_header_idx("fiscal year start month", "fiscal_year_start_month", "fiscal month")
        idx_favicon = get_header_idx("favicon url", "favicon_url")
        idx_logo = get_header_idx("logo url", "logo_url")
        idx_banner = get_header_idx("banner url", "banner_url")
        idx_status = get_header_idx("status", "status_type")
        idx_note = get_header_idx("note", "note / remarks", "remarks")

        if idx_cid == -1 or idx_name == -1:
            flash.set("Required header columns missing: 'Company ID (CID)' and 'Company Name' are required.", "danger")
            return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

        # Pre-fetch existing companies map
        comp_rows = db.executesql("SELECT id, cid FROM companies")
        existing_companies = {r[1].upper(): r[0] for r in comp_rows}

        total_cnt = 0
        created_cnt = 0
        updated_cnt = 0
        failed_cnt = 0
        errors = []

        current_user = session.user.get("username") or session.user.get("user_id") or "SYSTEM"

        for row_idx, r in enumerate(data_rows, start=2):
            if not any(cell.strip() for cell in r):
                continue
            total_cnt += 1

            def val_at(idx):
                if idx != -1 and idx < len(r):
                    v = r[idx].strip()
                    return v if v != "" else None
                return None

            r_cid = val_at(idx_cid)
            r_name = val_at(idx_name)

            if not r_cid:
                failed_cnt += 1
                errors.append({"row": row_idx, "cid": r_cid or "--", "error": "Company ID (CID) is missing."})
                continue
            if not r_name:
                failed_cnt += 1
                errors.append({"row": row_idx, "cid": r_cid, "error": "Company Name is missing."})
                continue

            r_cid = r_cid.upper()
            r_legal = val_at(idx_legal)
            r_email = val_at(idx_email)
            r_phone = val_at(idx_phone)
            r_website = val_at(idx_website)
            r_addr1 = val_at(idx_addr1)
            r_addr2 = val_at(idx_addr2)
            r_city = val_at(idx_city)
            r_state = val_at(idx_state)
            r_country = val_at(idx_country) or "Bangladesh"
            r_postal = val_at(idx_postal)
            r_tz = val_at(idx_tz) or "UTC+06:00"
            r_lang = val_at(idx_lang) or "en"
            
            raw_fiscal = val_at(idx_fiscal)
            try:
                r_fiscal = int(raw_fiscal) if raw_fiscal else 1
            except (ValueError, TypeError):
                r_fiscal = 1

            r_favicon = val_at(idx_favicon)
            r_logo = val_at(idx_logo)
            r_banner = val_at(idx_banner)
            raw_status = (val_at(idx_status) or "ACTIVE").upper()
            r_status = "ACTIVE" if raw_status in ["ACTIVE", "1", "TRUE", "ENABLED"] else "INACTIVE"
            r_note = val_at(idx_note)

            try:
                if r_cid in existing_companies:
                    # Update existing record (COALESCE preserves existing branding/language if omitted)
                    company_id = existing_companies[r_cid]
                    update_sql = """
                    UPDATE companies SET
                        company_name = %s, legal_name = %s, email = %s, phone = %s, website = %s,
                        address_line1 = %s, address_line2 = %s, city = %s, state = %s, country = %s, postal_code = %s,
                        timezone = %s, language_code = COALESCE(%s, language_code), fiscal_year_start_month = %s,
                        favicon_url = COALESCE(%s, favicon_url), logo_url = COALESCE(%s, logo_url), banner_url = COALESCE(%s, banner_url), status_type = %s, note = %s,
                        updated_on = NOW(), updated_by = %s
                    WHERE id = %s
                    """
                    db.executesql(update_sql, [
                        r_name, r_legal, r_email, r_phone, r_website,
                        r_addr1, r_addr2, r_city, r_state, r_country, r_postal,
                        r_tz, r_lang, r_fiscal,
                        r_favicon, r_logo, r_banner, r_status, r_note,
                        current_user, company_id
                    ])
                    updated_cnt += 1
                else:
                    # Insert new record
                    insert_sql = """
                    INSERT INTO companies (
                        cid, company_name, legal_name, email, phone, website,
                        address_line1, address_line2, city, state, country, postal_code,
                        timezone, language_code, fiscal_year_start_month,
                        favicon_url, logo_url, banner_url, status_type, note,
                        created_on, created_by
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        NOW(), %s
                    )
                    """
                    db.executesql(insert_sql, [
                        r_cid, r_name, r_legal, r_email, r_phone, r_website,
                        r_addr1, r_addr2, r_city, r_state, r_country, r_postal,
                        r_tz, r_lang, r_fiscal,
                        r_favicon, r_logo, r_banner, r_status, r_note,
                        current_user
                    ])
                    existing_companies[r_cid] = True
                    created_cnt += 1
            except Exception as e:
                failed_cnt += 1
                errors.append({"row": row_idx, "cid": r_cid, "error": str(e)})

        stats = {
            "total": total_cnt,
            "created": created_cnt,
            "updated": updated_cnt,
            "failed": failed_cnt,
            "errors": errors
        }
        flash.set(f"Import finished: {created_cnt} created, {updated_cnt} updated, {failed_cnt} failed.", "success" if failed_cnt == 0 else "warning")

    return dict(stats=stats, active_tab=active_tab)

@action("administration/roles_permisions", method=["GET", "POST"])
@view_page("administration/roles_permisions.html", title="Roles & Permissions | Administration")
@web_auth_required
def roles_permisions():
    action_type = (request.query.get("action") or "").strip().lower()
    delete_role_id = (request.query.get("delete_role_id") or request.query.get("role_id") or "").strip().upper()

    if action_type == "delete" and delete_role_id:
        try:
            db.executesql("UPDATE users SET role_id = NULL WHERE UPPER(role_id) = %s", [delete_role_id])
            db.executesql("DELETE FROM role_module_permissions WHERE UPPER(role_id) = %s", [delete_role_id])
            db.executesql("DELETE FROM roles WHERE UPPER(role_id) = %s", [delete_role_id])
            db.commit()
            try:
                from ..utils.menu_utils import clear_menu_cache
                clear_menu_cache()
            except Exception:
                pass

            flash.set(f"Role '{delete_role_id}' deleted successfully.", "success")

        except Exception as e:
            flash.set(f"Error deleting role: {str(e)}", "danger")

        redirect(URL("administration/roles_permisions"))

    roles_rows = db.executesql(
        "SELECT id, cid, role_id, role_name, note as description FROM roles WHERE status_type = 'ACTIVE' ORDER BY id ASC",
        as_dict=True
    )

    all_mods = db.executesql(
        "SELECT module_id, module_name, parent_module_id, module_group, icon as module_icon, is_clickable FROM modules WHERE status_type = 'ACTIVE' ORDER BY display_order ASC",
        as_dict=True
    )
    parent_map = {m["module_id"]: m["module_name"] for m in all_mods if not m["is_clickable"]}

    all_roles = []
    for r in roles_rows:
        role_id = r["role_id"]
        perm_rows = db.executesql(
            """SELECT p.*, m.module_name, m.parent_module_id, m.module_group, m.icon as module_icon, m.is_clickable
               FROM role_module_permissions p
               JOIN modules m ON p.module_id = m.module_id
               WHERE p.role_id = %s AND (p.status_type IS NULL OR p.status_type = 'ACTIVE') AND (m.status_type IS NULL OR m.status_type = 'ACTIVE') AND m.is_clickable = 1
               ORDER BY m.display_order ASC""",
            [role_id],
            as_dict=True
        )

        groups_dict = {}
        for p in perm_rows:
            can_v = bool(p.get("can_view"))
            can_c = bool(p.get("can_add") or p.get("can_create"))
            can_e = bool(p.get("can_edit"))
            can_d = bool(p.get("can_delete"))
            can_ex = bool(p.get("can_export"))
            can_app = bool(p.get("can_approve"))

            if not (can_v or can_c or can_e or can_d or can_ex or can_app):
                continue

            p_id = p.get("parent_module_id")
            g_name = parent_map.get(p_id) or p.get("module_group") or "General"
            if g_name not in groups_dict:
                groups_dict[g_name] = {"module_group": g_name, "modules": []}
            
            groups_dict[g_name]["modules"].append({
                "module_id": p.get("module_id"),
                "module_name": p.get("module_name"),
                "module_icon": p.get("module_icon") or "extension",
                "can_view": can_v,
                "can_create": can_c,
                "can_edit": can_e,
                "can_delete": can_d,
                "can_export": can_ex,
                "can_approve": can_app,
            })

        r["permissions"] = list(groups_dict.values())
        all_roles.append(r)

    selected_role_id = str(request.query.get("role_id") or request.params.get("role_id") or "").strip()
    return dict(all_roles=all_roles, selected_role_id=selected_role_id)


@action("administration/role_manage", method=["GET", "POST"])
@action("administration/role_manage/<role_id>", method=["GET", "POST"])
@view_page("administration/role_manage.html", title="Role Management | Administration")
@web_auth_required
def role_manage(role_id=None):
    user_id = session.user.get("user_id", "SYSTEM") if (session and session.user) else "SYSTEM"
    db_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "POST":
        data = request.json if request.json else request.forms
        raw_role_id = str(data.get("role_id") or "").strip().upper()
        custom_role_id = str(data.get("custom_role_id") or "").strip().upper()
        cid = str(data.get("cid") or "").strip().upper() or None
        role_name = str(data.get("role_name") or "").strip()
        description = str(data.get("description") or "").strip()
        status_type = str(data.get("status_type") or "ACTIVE").strip().upper()

        permissions = data.get("permissions")
        if not permissions and "permissions_json" in data:
            perm_raw = data.get("permissions_json")
            if isinstance(perm_raw, str) and perm_raw.strip():
                try:
                    import json
                    permissions = json.loads(perm_raw)
                except Exception:
                    permissions = []
            elif isinstance(perm_raw, list):
                permissions = perm_raw
        if not permissions or not isinstance(permissions, list):
            permissions = []

        if not role_name:
            flash.set("Role Name is required.", "danger")
            redirect(URL("administration/role_manage"))

        if raw_role_id:
            # Updating existing role
            target_role_id = raw_role_id
            db.executesql(
                "UPDATE roles SET cid = %s, role_name = %s, note = %s, status_type = %s, updated_on = %s, updated_by = %s WHERE role_id = %s",
                [cid, role_name, description, status_type, db_datetime, user_id, target_role_id]
            )
        else:
            # Creating new role
            target_role_id = custom_role_id
            if not target_role_id:
                import re
                slug = "".join([c if c.isalnum() else "_" for c in role_name.upper()]).strip("_")
                slug = re.sub(r"_+", "_", slug)
                target_role_id = slug if slug else "NEW_ROLE"
            
            target_role_id = target_role_id.upper()[:30]

            # Check if role_id and cid combination already exists
            if cid:
                check_exist = db.executesql(
                    "SELECT role_id FROM roles WHERE role_id = %s AND cid = %s LIMIT 1",
                    [target_role_id, cid],
                    as_dict=True
                )
            else:
                check_exist = db.executesql(
                    "SELECT role_id FROM roles WHERE role_id = %s AND (cid IS NULL OR cid = '') LIMIT 1",
                    [target_role_id],
                    as_dict=True
                )

            if check_exist:
                scope_name = f"Company '{cid}'" if cid else "Global scope"
                flash.set(f"Role ID '{target_role_id}' already exists for {scope_name}. Duplicate role creation is not allowed.", "danger")
                redirect(URL("administration/role_manage"))

            db.executesql(
                "INSERT INTO roles (cid, role_id, role_name, note, status_type, created_on, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [cid, target_role_id, role_name, description, status_type, db_datetime, user_id]
            )

        # Re-insert role module permissions
        db.executesql("DELETE FROM role_module_permissions WHERE role_id = %s", [target_role_id])

        for perm in permissions:
            if not isinstance(perm, dict):
                continue
            mod_id = perm.get("module_id")
            if not mod_id:
                continue
            can_v = 1 if perm.get("can_view") else 0
            can_c = 1 if (perm.get("can_create") or perm.get("can_add")) else 0
            can_e = 1 if perm.get("can_edit") else 0
            can_d = 1 if perm.get("can_delete") else 0
            can_ex = 1 if perm.get("can_export") else 0
            can_app = 1 if perm.get("can_approve") else 0

            db.executesql(
                """INSERT INTO role_module_permissions
                   (role_id, module_id, can_view, can_add, can_edit, can_delete, can_export, can_approve, status_type, created_on, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [target_role_id, mod_id, can_v, can_c, can_e, can_d, can_ex, can_app, status_type, db_datetime, user_id]
            )

        db.commit()

        try:
            from ..utils.menu_utils import clear_menu_cache
            clear_menu_cache()
        except Exception:
            pass

        action_msg = "updated" if raw_role_id else "created"
        flash.set(f"Role '{role_name}' {action_msg} successfully!", "success")
        redirect(URL("administration/roles_permisions", vars=dict(role_id=target_role_id)))

    # GET Request
    role_id = role_id or request.query.get("role_id") or request.params.get("role_id") or ""
    cid = ""
    role_name = ""
    description = ""
    status_type = "ACTIVE"

    if role_id:
        r_rows = db.executesql("SELECT cid, role_id, role_name, note as description, status_type FROM roles WHERE role_id = %s LIMIT 1", [role_id], as_dict=True)
        if r_rows:
            cid = r_rows[0].get("cid", "") or ""
            role_name = r_rows[0].get("role_name", "")
            description = r_rows[0].get("description", "")
            status_type = r_rows[0].get("status_type", "ACTIVE") or "ACTIVE"

    companies = db.executesql("SELECT cid, company_name FROM companies WHERE status_type = 'ACTIVE' ORDER BY company_name ASC", as_dict=True)

    all_mods = db.executesql(
        "SELECT module_id, module_name, parent_module_id, module_group, icon as module_icon, is_clickable FROM modules WHERE status_type = 'ACTIVE' ORDER BY display_order ASC",
        as_dict=True
    )
    parent_map = {m["module_id"]: m["module_name"] for m in all_mods if not m["is_clickable"]}
    clickable_mods = [m for m in all_mods if m["is_clickable"]]

    if not clickable_mods:
        clickable_mods = [
            {"module_id": "DASHBOARD", "module_name": "Dashboard", "parent_module_id": None, "module_group": "General", "module_icon": "dashboard"},
            {"module_id": "EMPLOYEE_DIR", "module_name": "Employee Directory", "parent_module_id": "EMP_MGMT", "module_group": "HR", "module_icon": "badge"},
            {"module_id": "POSTING_TRANS", "module_name": "Postings & Transfers", "parent_module_id": "EMP_MGMT", "module_group": "HR", "module_icon": "swap_horiz"},
            {"module_id": "COMPANY_MGMT", "module_name": "Company Management", "parent_module_id": "ADMINISTRATION", "module_group": "System", "module_icon": "domain"},
            {"module_id": "ROLES_PERM", "module_name": "Roles & Permissions", "parent_module_id": "ADMINISTRATION", "module_group": "System", "module_icon": "key"},
            {"module_id": "USER_MGMT", "module_name": "User Management", "parent_module_id": "ADMINISTRATION", "module_group": "System", "module_icon": "manage_accounts"},
            {"module_id": "AUDIT_LOGS", "module_name": "Audit Logs", "parent_module_id": "ADMINISTRATION", "module_group": "System", "module_icon": "history"},
            {"module_id": "EMP_REPORTS", "module_name": "Employee Reports", "parent_module_id": "REPORTS_ANALYTICS", "module_group": "Reports", "module_icon": "description"},
            {"module_id": "TRANSFER_LOGS", "module_name": "Movement & Transfer Logs", "parent_module_id": "REPORTS_ANALYTICS", "module_group": "Reports", "module_icon": "receipt_long"},
        ]

    existing_perms = {}
    if role_id:
        p_rows = db.executesql(
            "SELECT module_id, can_view, can_add, can_edit, can_delete, can_export, can_approve FROM role_module_permissions WHERE role_id = %s",
            [role_id],
            as_dict=True
        )
        for p in p_rows:
            existing_perms[p["module_id"]] = p

    groups_map = {}
    for m in clickable_mods:
        p_id = m.get("parent_module_id")
        g_name = parent_map.get(p_id) or m.get("module_group") or "General"
        if g_name not in groups_map:
            groups_map[g_name] = {"module_group": g_name, "modules": []}
        
        m_id = m.get("module_id")
        p = existing_perms.get(m_id, {})
        groups_map[g_name]["modules"].append({
            "module_id": m_id,
            "module_name": m.get("module_name"),
            "module_icon": m.get("module_icon") or "extension",
            "can_view": bool(p.get("can_view", False)),
            "can_create": bool(p.get("can_add", False) or p.get("can_create", False)),
            "can_edit": bool(p.get("can_edit", False)),
            "can_delete": bool(p.get("can_delete", False)),
            "can_export": bool(p.get("can_export", False)),
            "can_approve": bool(p.get("can_approve", False)),
        })

    module_groups = list(groups_map.values())

    return dict(
        role_id=role_id,
        cid=cid,
        companies=companies,
        role_name=role_name,
        description=description,
        status_type=status_type,
        module_groups=module_groups,
    )

@action("administration/users")
@view_page("administration/users.html", title="User Management | Administration")
@web_auth_required
def users():
    user_cid = session.user.get("cid", "")
    action_type = request.query.get("action", "").strip().lower()
    delete_id = request.query.get("id") or request.query.get("delete_id")

    if action_type == "delete" and delete_id:
        try:
            del_id = int(delete_id)
            del_where = ["id = %s"]
            del_params = [del_id]
            if user_cid:
                del_where.append("LOWER(cid) = LOWER(%s)")
                del_params.append(user_cid)
            
            db.executesql(f"DELETE FROM users WHERE {' AND '.join(del_where)}", del_params)
            db.commit()
            flash.set("User account deleted successfully!", "success")
        except Exception as e:
            flash.set(f"Failed to delete user: {str(e)}", "danger")
        redirect(URL('administration/users'))

    keywords = request.query.get("keywords", "").strip()
    role = request.query.get("role", "").strip()
    status = request.query.get("status", "").strip()
    cid = user_cid if user_cid else request.query.get("cid", "").strip()
    export_format = request.query.get("export", "").strip().lower()

    # Build SQL WHERE conditions
    where_clauses = ["1=1"]
    params = []

    if cid:
        where_clauses.append("LOWER(u.cid) = LOWER(%s)")
        params.append(cid)

    if keywords:
        where_clauses.append("(u.user_id LIKE %s OR u.user_name LIKE %s OR u.email LIKE %s OR e.emp_department LIKE %s OR b.branch_name LIKE %s)")
        kw_pattern = f"%{keywords}%"
        params.extend([kw_pattern, kw_pattern, kw_pattern, kw_pattern, kw_pattern])

    if role:
        where_clauses.append("UPPER(u.role_id) = %s")
        params.append(role.upper())

    if status:
        where_clauses.append("UPPER(u.status_type) = %s")
        params.append(status.upper())

    where_str = " AND ".join(where_clauses)

    user_records_sql = f"""
        SELECT 
            u.id, 
            COALESCE(u.cid, '') AS cid,
            u.user_id, 
            u.user_name, 
            COALESCE(u.email, e.email, '--') AS user_email, 
            COALESCE(u.mobile, e.mobile, '--') AS mobile,
            COALESCE(e.emp_department, '--') AS department, 
            COALESCE(e.emp_designation, '--') AS designation, 
            COALESCE(b.branch_name, e.current_branch_id, '--') AS branch, 
            u.last_login_on AS last_login, 
            u.role_id AS user_role, 
            u.status_type AS user_status,
            COALESCE(u.profile_image, e.photo_url, '') AS user_photo
        FROM users u
        LEFT JOIN employees e ON u.emp_id = e.emp_id AND (u.cid IS NULL OR LOWER(u.cid) = LOWER(e.cid))
        LEFT JOIN branches b ON e.current_branch_id = b.branch_id AND (e.cid IS NULL OR LOWER(e.cid) = LOWER(b.cid))
        WHERE {where_str}
        ORDER BY u.id DESC; 
    """
    try:
        raw_users = db.executesql(user_records_sql, params, as_dict=True)
    except Exception:
        raw_users = []

    # Format last_login if datetime object
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

    # Export Handling
    if export_format in ["xlsx", "xls", "csv"]:
        filename = f"User_List_{db_datetime.strftime('%Y%m%d_%H%M%S')}"
        if not user_cid:
            headers = ["ID", "Company ID (CID)", "User ID", "Full Name", "Email Address", "Department", "Designation", "Branch", "Role", "Status", "Last Login"]
        else:
            headers = ["ID", "User ID", "Full Name", "Email Address", "Department", "Designation", "Branch", "Role", "Status", "Last Login"]

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for u in raw_users:
                row_vals = [u.get("id", "")]
                if not user_cid:
                    row_vals.append(u.get("cid", ""))
                row_vals.extend([
                    u.get("user_id", ""), u.get("user_name", ""), u.get("user_email", ""),
                    u.get("department", ""), u.get("designation", ""), u.get("branch", ""),
                    u.get("user_role", ""), u.get("user_status", ""), u.get("last_login", "")
                ])
                writer.writerow(row_vals)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return output.getvalue()

        if export_format in ["xlsx", "xls"]:
            xml_data = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?mso-application progid="Excel.Sheet"?>',
                '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">',
                '<Styles>',
                '<Style ss:ID="HeaderStyle"><Font ss:FontName="Calibri" ss:Size="11" ss:Color="#FFFFFF" ss:Bold="1"/><Interior ss:Color="#0F172A" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/></Style>',
                '<Style ss:ID="DataLeft"><Font ss:FontName="Calibri" ss:Size="10"/><Alignment ss:Horizontal="Left" ss:Vertical="Center"/></Style>',
                '<Style ss:ID="DataCenter"><Font ss:FontName="Calibri" ss:Size="10"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/></Style>',
                '</Styles>',
                '<Worksheet ss:Name="Users"><Table>',
                '<Row ss:Height="26">'
            ]
            for h in headers:
                xml_data.append(f'  <Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{xml_escape.escape(h)}</Data></Cell>')
            xml_data.append('</Row>')
            for u in raw_users:
                xml_data.append('<Row ss:Height="22">')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{u.get("id", "")}</Data></Cell>')
                if not user_cid:
                    xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{xml_escape.escape(str(u.get("cid", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{xml_escape.escape(str(u.get("user_id", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{xml_escape.escape(str(u.get("user_name", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{xml_escape.escape(str(u.get("user_email", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{xml_escape.escape(str(u.get("department", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{xml_escape.escape(str(u.get("designation", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataLeft"><Data ss:Type="String">{xml_escape.escape(str(u.get("branch", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{xml_escape.escape(str(u.get("user_role", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{xml_escape.escape(str(u.get("user_status", "")))}</Data></Cell>')
                xml_data.append(f'  <Cell ss:StyleID="DataCenter"><Data ss:Type="String">{xml_escape.escape(str(u.get("last_login", "")))}</Data></Cell>')
                xml_data.append('</Row>')
            xml_data.append('</Table></Worksheet></Workbook>')
            response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
            return "\n".join(xml_data)

    # Stats Calculation
    stats_sql = "SELECT COUNT(*) as total, SUM(CASE WHEN UPPER(status_type) = 'ACTIVE' THEN 1 ELSE 0 END) as active, SUM(CASE WHEN UPPER(status_type) IN ('INACTIVE', 'LOCKED', 'BLOCKED') THEN 1 ELSE 0 END) as inactive, SUM(CASE WHEN UPPER(role_id) LIKE %s THEN 1 ELSE 0 END) as admin FROM users WHERE 1=1"
    stats_params = ['%ADMIN%']
    if cid:
        stats_sql += " AND LOWER(cid) = LOWER(%s)"
        stats_params.append(cid)
    
    stats_res = db.executesql(stats_sql, stats_params, as_dict=True)
    st = stats_res[0] if stats_res else {}
    stats = {
        "total": st.get("total") or 0,
        "active": st.get("active") or 0,
        "inactive": st.get("inactive") or 0,
        "admin": st.get("admin") or 0,
    }

    # Limit and Pagination Logic
    try:
        limit = max(1, int(request.query.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    total_filtered = len(raw_users)
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
    paginated_users = raw_users[start_idx:end_idx]

    pagination = {
        "current_page": page,
        "limit": limit,
        "page_size": limit,
        "total_pages": total_pages,
        "total_items": total_filtered,
        "start_item": start_idx + 1 if total_filtered > 0 else 0,
        "end_item": min(end_idx, total_filtered),
    }

    return dict(
        all_users=paginated_users, 
        stats=stats, 
        pagination=pagination,
        user_cid=user_cid
    )


@action("administration/import_users", method=["GET", "POST"])
@view_page("administration/import_users.html", title="Import Users | Administration")
@web_auth_required
def import_users():
    user_cid = session.user.get("cid", "")
    if request.query.get("template") == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        if not user_cid:
            writer.writerow(["Company ID", "User ID", "Full Name", "Password", "Email", "Mobile", "Status"])
            writer.writerow(["BADC", "badc_officer", "Jamal Hossain", "123456", "jamal@badc.gov.bd", "+8801700000000", "ACTIVE"])
        else:
            writer.writerow(["User ID", "Full Name", "Password", "Email", "Mobile", "Status"])
            writer.writerow(["badc_officer", "Jamal Hossain", "123456", "jamal@badc.gov.bd", "+8801700000000", "ACTIVE"])
        
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="User_Import_Template.csv"'
        return output.getvalue()

    stats = None
    active_tab = "file"

    if request.method == "POST":
        csv_file = request.files.get("csv_file")
        csv_text = request.forms.get("csv_text")
        content = None
        delimiter = ','
        is_sys_admin = not user_cid
        max_file_mb = 10 if is_sys_admin else 2
        max_rows = 10000 if is_sys_admin else 1000

        if csv_file and csv_file.filename:
            active_tab = "file"
            if not csv_file.filename.lower().endswith('.csv'):
                flash.set("Only CSV files are allowed.", "danger")
            file_bytes = csv_file.file.read()
            if len(file_bytes) > max_file_mb * 1024 * 1024:
                flash.set(f"File size exceeds maximum limit of {max_file_mb}MB.", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
            
            try:
                content = file_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    content = file_bytes.decode('latin1')
                except Exception:
                    flash.set("Failed to decode file encoding. Please ensure standard UTF-8 CSV.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
            
            first_line = content.splitlines()[0] if content else ""
            if '\t' in first_line:
                delimiter = '\t'
            elif ';' in first_line and ',' not in first_line:
                delimiter = ';'

        elif csv_text and csv_text.strip():
            active_tab = "text"
            if len(csv_text.encode('utf-8')) > max_file_mb * 1024 * 1024:
                flash.set(f"Content size exceeds limit of {max_file_mb}MB.", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
            content = csv_text.strip()
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
            raw_headers = reader.fieldnames or []
            headers_clean = [h.strip().lower() for h in raw_headers if h]

            def has_header(*aliases):
                return any(alias in headers_clean for alias in aliases)

            if not user_cid:
                if not has_header('cid', 'company id', 'company_id') or \
                   not has_header('user_id', 'login id', 'user id', 'username') or \
                   not has_header('user_name', 'full name', 'name', 'user name'):
                    flash.set("Invalid CSV format. Missing required columns: 'cid', 'user_id', and 'user_name'.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)
            else:
                if not has_header('user_id', 'login id', 'user id', 'username') or \
                   not has_header('user_name', 'full name', 'name', 'user name'):
                    flash.set("Invalid CSV format. Missing required columns: 'user_id' and 'user_name'.", "danger")
                    return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

            created_cnt = 0
            updated_cnt = 0
            failed_cnt = 0
            errors_list = []

            rows = list(reader)
            if len(rows) > max_rows:
                flash.set(f"Data exceeds maximum allowed limit of {max_rows:,} rows.", "danger")
                return dict(stats=None, active_tab=active_tab, user_cid=user_cid)

            for idx, r in enumerate(rows, start=1):
                def get_val(*aliases):
                    for k, v in r.items():
                        if k and k.strip().lower() in aliases:
                            return (v or '').strip()
                    return ''

                row_cid = user_cid if user_cid else get_val('cid', 'company id', 'company_id')
                r_user_id = get_val('user_id', 'login id', 'user id', 'username')
                r_name = get_val('user_name', 'full name', 'name', 'user name')
                r_pass = get_val('user_pass', 'password', 'pass') or '123456'
                r_email = get_val('email', 'user_email', 'email address')
                r_mobile = get_val('mobile', 'phone', 'contact')
                r_status = (get_val('status_type', 'status') or 'ACTIVE').upper()

                if not r_user_id or not r_name:
                    failed_cnt += 1
                    errors_list.append({"row": idx, "emp_id": r_user_id or f"Row {idx}", "error": "Missing User ID or Full Name"})
                    continue

                try:
                    chk = db.executesql("SELECT id FROM users WHERE UPPER(user_id) = %s LIMIT 1", [r_user_id.upper()], as_dict=True)
                    if chk:
                        db.executesql("""
                            UPDATE users SET 
                                cid = COALESCE(NULLIF(%s, ''), cid),
                                user_name = %s,
                                email = %s,
                                mobile = %s,
                                status_type = %s
                            WHERE UPPER(user_id) = %s
                        """, [row_cid, r_name, r_email, r_mobile, r_status, r_user_id.upper()])
                        updated_cnt += 1
                    else:
                        db.executesql("""
                            INSERT INTO users (cid, user_id, user_name, user_pass, email, mobile, status_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, [row_cid, r_user_id, r_name, r_pass, r_email, r_mobile, r_status])
                        created_cnt += 1
                except Exception as row_err:
                    print("User import row error:", row_err)
                    failed_cnt += 1
                    errors_list.append({"row": idx, "emp_id": r_user_id, "error": str(row_err)})

            db.commit()
            stats = {"total": len(rows), "created": created_cnt, "updated": updated_cnt, "failed": failed_cnt, "errors": errors_list}
            if failed_cnt > 0:
                flash.set(f"Import completed with warnings. Created: {created_cnt}, Updated: {updated_cnt}, Failed: {failed_cnt}", "warning")
            else:
                flash.set(f"Successfully imported {created_cnt + updated_cnt} user accounts! (Created: {created_cnt}, Updated: {updated_cnt})", "success")

        except Exception as e:
            flash.set(f"Failed to process CSV data: {str(e)}", "danger")

    return dict(stats=stats, active_tab=active_tab, user_cid=user_cid)


@action("administration/user_manage", method=["GET", "POST"])
@action("administration/user_manage/<user_id>", method=["GET", "POST"])
@action("administration/add_user", method=["GET", "POST"])
@action("administration/edit_user", method=["GET", "POST"])
@action("administration/edit_user/<user_id>", method=["GET", "POST"])
@view_page("administration/user_manage.html", title="User Management | Administration")
@web_auth_required
def user_manage(user_id=None):
    user_cid = session.user.get("cid", "")
    current_user_id = session.user.get("user_id", "SYSTEM")

    if user_id is None:
        user_id = request.query.get("id") or request.query.get("user_id") or request.query.get("edit_id")

    target_user = None
    if user_id:
        if str(user_id).isdigit():
            user_rows = db.executesql("""
                SELECT u.*, e.emp_name, e.emp_designation, e.emp_department, e.photo_url as emp_photo, e.mobile as emp_mobile, e.email as emp_email
                FROM users u
                LEFT JOIN employees e ON u.emp_id = e.emp_id AND (u.cid IS NULL OR LOWER(u.cid) = LOWER(e.cid))
                WHERE u.id = %s OR UPPER(u.user_id) = %s
                LIMIT 1
            """, [int(user_id), str(user_id).upper()], as_dict=True)
        else:
            user_rows = db.executesql("""
                SELECT u.*, e.emp_name, e.emp_designation, e.emp_department, e.photo_url as emp_photo, e.mobile as emp_mobile, e.email as emp_email
                FROM users u
                LEFT JOIN employees e ON u.emp_id = e.emp_id AND (u.cid IS NULL OR LOWER(u.cid) = LOWER(e.cid))
                WHERE UPPER(u.user_id) = %s
                LIMIT 1
            """, [str(user_id).upper()], as_dict=True)

        if user_rows:
            target_user = user_rows[0]
        else:
            flash.set(f"User account '{user_id}' not found.", "danger")
            redirect(URL("administration/users"))

    mode = request.query.get("mode", "")

    # Handle AJAX Employee Lookup inside user_manage
    if request.query.get("action") == "lookup":
        import json
        response.headers['Content-Type'] = 'application/json'
        emp_id = (request.query.get("emp_id") or request.params.get("emp_id") or "").strip()
        cid = (request.query.get("cid") or request.params.get("cid") or user_cid or "").strip()

        if not emp_id:
            return json.dumps(dict(success=False, message="Please enter an Official ID to search."))

        where_clauses = ["UPPER(emp_id) = %s"]
        params = [emp_id.upper()]
        if cid:
            where_clauses.append("UPPER(cid) = %s")
            params.append(cid.upper())

        try:
            sql = f"""
                SELECT emp_id, emp_name, mobile, email, cid, emp_designation, emp_department, photo_url, status_type
                FROM employees
                WHERE {' AND '.join(where_clauses)}
                LIMIT 1
            """
            res = db.executesql(sql, params, as_dict=True)
            if res:
                emp = res[0]
                return json.dumps(dict(success=True, employee=emp))
            else:
                return json.dumps(dict(success=False, message=f"No record found with ID '{emp_id}'"))
        except Exception as e:
            return json.dumps(dict(success=False, message=str(e)))

    if request.method == "POST":
        creation_mode = request.forms.get("creation_mode", "direct")
        target_cid = user_cid or request.forms.get("cid", "").strip()
        selected_emp_id = request.forms.get("lookup_emp_id", "").strip() or request.forms.get("emp_id", "").strip()
        
        r_user_id = request.forms.get("user_id", "").strip()
        r_full_name = request.forms.get("full_name", "").strip()
        r_mobile = request.forms.get("mobile", "").strip()
        r_email = request.forms.get("email", "").strip()
        
        r_password = request.forms.get("password", "").strip()
        r_confirm_password = request.forms.get("confirm_password", "").strip()
        
        r_role = request.forms.get("role", "").strip().upper()
        r_status = (request.forms.get("status") or "ACTIVE").strip().upper()
        r_note = request.forms.get("note", "").strip()

        avatar_file = request.files.get("avatar")
        remove_avatar = request.forms.get("remove_avatar") == "1"

        if r_password and r_confirm_password and r_password != r_confirm_password:
            flash.set("Passwords do not match. Please try again.", "danger")
            redirect(URL("administration/user_manage", vars={'id': target_user['id']} if target_user else {}))

        if target_user:
            # Edit existing user
            if target_user.get("emp_id"):
                r_full_name = target_user.get("emp_name") or target_user.get("user_name") or "User"
                r_email = target_user.get("emp_email") or target_user.get("email") or r_email
                r_mobile = target_user.get("emp_mobile") or target_user.get("mobile") or r_mobile

            if not r_full_name:
                flash.set("Full Name is required.", "danger")
                redirect(URL("administration/user_manage", vars={'id': target_user['id']}))

            uploaded_avatar = _save_user_avatar_file(avatar_file, target_user.get("user_id", r_user_id))

            emp_id_to_link = None
            if creation_mode == "employee" and selected_emp_id:
                emp_id_to_link = selected_emp_id
            elif target_user.get("emp_id"):
                emp_id_to_link = target_user.get("emp_id")

            try:
                update_fields = [
                    "cid = COALESCE(NULLIF(%s, ''), cid)",
                    "user_name = %s",
                    "email = %s",
                    "mobile = %s",
                    "role_id = NULLIF(%s, '')",
                    "emp_id = NULLIF(%s, '')",
                    "note = %s",
                    "status_type = %s",
                    "updated_on = %s",
                    "updated_by = %s"
                ]
                params = [target_cid, r_full_name, r_email, r_mobile, r_role, emp_id_to_link or '', r_note, r_status, db_datetime, current_user_id]

                if r_password:
                    update_fields.append("user_pass = %s")
                    params.append(r_password)

                if uploaded_avatar:
                    update_fields.append("profile_image = %s")
                    params.append(uploaded_avatar)
                elif remove_avatar:
                    update_fields.append("profile_image = NULL")

                params.append(target_user["id"])

                sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                db.executesql(sql, params)
                db.commit()
                flash.set(f"User account '{r_full_name}' ({target_user.get('user_id')}) updated successfully!", "success")
                redirect(URL("administration/users"))
            except Exception as e:
                flash.set(f"Failed to update user account: {str(e)}", "danger")
                redirect(URL("administration/user_manage", vars={'id': target_user['id']}))
        else:
            # Add new user
            if not r_user_id or not r_full_name:
                flash.set("User ID and Full Name are required.", "danger")
                redirect(URL("administration/user_manage"))

            if not r_password:
                r_password = "123456"

            chk = db.executesql("SELECT id FROM users WHERE UPPER(user_id) = %s LIMIT 1", [r_user_id.upper()], as_dict=True)
            if chk:
                flash.set(f"User ID '{r_user_id}' already exists! Please use a different User ID.", "danger")
                redirect(URL("administration/user_manage"))

            uploaded_avatar = _save_user_avatar_file(avatar_file, r_user_id)
            emp_id_to_link = selected_emp_id if (creation_mode == "employee" and selected_emp_id) else None

            try:
                db.executesql("""
                    INSERT INTO users (cid, user_id, user_name, user_pass, role_id, emp_id, email, mobile, note, status_type, profile_image, created_on, created_by)
                    VALUES (%s, %s, %s, %s, NULLIF(%s, ''), NULLIF(%s, ''), %s, %s, %s, %s, %s, %s, %s)
                """, [target_cid, r_user_id, r_full_name, r_password, r_role, emp_id_to_link, r_email, r_mobile, r_note, r_status, uploaded_avatar, db_datetime, current_user_id])
                db.commit()
                flash.set(f"User account '{r_full_name}' ({r_user_id}) created successfully!", "success")
                redirect(URL("administration/users"))
            except Exception as e:
                flash.set(f"Failed to create user account: {str(e)}", "danger")
                redirect(URL("administration/user_manage"))

    roles_rows = db.executesql("""
        SELECT role_id, role_name, cid FROM roles WHERE status_type = 'ACTIVE' ORDER BY role_name ASC
    """, as_dict=True)

    page_title = "Edit User" if target_user else "Add User"

    return dict(
        user_cid=user_cid,
        roles=roles_rows,
        target_user=target_user,
        page_title=page_title,
        mode=mode
    )

