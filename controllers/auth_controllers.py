from py4web import URL, request, redirect, action
import time

@action("auth/login", method=["GET", "POST"])
@action.uses("auth/login.html") # আপনার ফাইলের নাম login.html হলে এখানে শুধু login.html হবে
def login():
    error = None
    page_title = "Login | HRMS Admin"
    
    if request.method == "POST":
        username = request.forms.get("username")
        password = request.forms.get("password")
        time.sleep(1) # টেস্ট করার জন্য ১ সেকেন্ড দেওয়াই ভালো, ৫ সেকেন্ড অনেক বেশি লাগে ভাই
        
        if username == "admin@hrms.com" and password == "admin123":
            redirect(URL("dashboard"))
        else:
            error = "Invalid User ID or Password. Please try again."
            
    return dict(
        error=error, 
        page_title=page_title
    )


@action("dashboard")
@action.uses("dashboard.html") # ✅ এখন এটি পারফেক্টলি layout.html কে সাথে নিয়ে লোড হবে
def dashboard():
    page_title = "Dashboard | HRMS"
    return dict(page_title=page_title)


@action("employees")
@action.uses("employees.html") # ✅ চাইল্ড পেজের নাম দিন
def employees():
    page_title = "Employees Management | HRMS"
    return dict(page_title=page_title)


@action("attendance")
@action.uses("attendance.html") # ✅ চাইল্ড পেজের নাম দিন
def attendance():
    page_title = "Attendance | HRMS"
    return dict(page_title=page_title)