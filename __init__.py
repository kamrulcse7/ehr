from py4web import action, redirect, URL

from .controllers import auth, dashboard, administration


@action("index")
def index():
    redirect(URL("dashboard"))