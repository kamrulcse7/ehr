from py4web import action, redirect, URL

from .controllers import auth, dashboard, administration, employees


@action("index")
def index():
    redirect(URL("dashboard"))