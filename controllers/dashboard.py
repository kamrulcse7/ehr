from py4web import URL, action, redirect, request
from ..middleware.auth_middleware import web_auth_required
from ..utils.common import db, flash, session, view_page


@action("dashboard/index")
@view_page("dashboard/index.html")
@web_auth_required
def dashboard():
    page_title = "Dashboard | Enterprise HRMS"

    # Enhanced Key Performance Indicators
    stats = {
        "total_employees": "12,482",
        "employee_growth": "+2.4%",
        "active_transfers": "1,840",
        "pending_transfers": "127",
        "total_divisions": "8 Divisions",
    }

    # Division distribution for visual progress bars
    division_stats = [
        {"name": "Dhaka HQ", "count": 4200, "percentage": 34, "color": "bg-indigo-600"},
        {"name": "Chittagong", "count": 2800, "percentage": 22, "color": "bg-blue-500"},
        {"name": "Rajshahi", "count": 1900, "percentage": 15, "color": "bg-emerald-500"},
        {"name": "Sylhet", "count": 1500, "percentage": 12, "color": "bg-amber-500"},
        {"name": "Others", "count": 2082, "percentage": 17, "color": "bg-slate-400"},
    ]

    recent_employees = [
        {"name": "Arif Hasan", "role": "Software Engineer", "division": "Dhaka Div", "joined": "Today", "avatar_bg": "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-300"},
        {"name": "Nusrat Jahan", "role": "HR Executive", "division": "Chittagong Div", "joined": "Yesterday", "avatar_bg": "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300"},
        {"name": "Tanvir Ahmed", "role": "Accounts Officer", "division": "Rajshahi Div", "joined": "2 days ago", "avatar_bg": "bg-amber-100 text-amber-700 dark:bg-amber-950/70 dark:text-amber-300"},
        {"name": "Sultana Razia", "role": "Assistant Director", "division": "Sylhet Div", "joined": "3 days ago", "avatar_bg": "bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300"},
    ]

    recent_transfers = [
        {
            "id": "TR-45821",
            "name": "S.M. Rahman",
            "designation": "Assistant Director",
            "from_loc": "Dhaka HQ",
            "to_loc": "Chittagong Div",
            "date": "24 Oct, 2026",
            "status": "Completed",
        },
        {
            "id": "TR-45822",
            "name": "Anisul Islam",
            "designation": "Senior Officer",
            "from_loc": "Rajshahi Div",
            "to_loc": "Sylhet Div",
            "date": "25 Oct, 2026",
            "status": "Processing",
        },
        {
            "id": "TR-45823",
            "name": "Fatima Begum",
            "designation": "Executive Officer",
            "from_loc": "Khulna Div",
            "to_loc": "Dhaka HQ",
            "date": "25 Oct, 2026",
            "status": "Pending",
        },
        {
            "id": "TR-45824",
            "name": "Zakir Hossain",
            "designation": "Administrative Officer",
            "from_loc": "Barisal Div",
            "to_loc": "Dhaka HQ",
            "date": "26 Oct, 2026",
            "status": "Completed",
        },
        {
            "id": "TR-45825",
            "name": "Farhana Yeasmin",
            "designation": "Senior Officer",
            "from_loc": "Dhaka HQ",
            "to_loc": "Mymensingh Div",
            "date": "26 Oct, 2026",
            "status": "Completed",
        },
    ]

    return dict(
        page_title=page_title,
        session=session,
        stats=stats,
        division_stats=division_stats,
        recent_employees=recent_employees,
        recent_transfers=recent_transfers,
    )