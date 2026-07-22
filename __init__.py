from py4web import action, redirect, URL

from .controllers import auth_controllers

@action("index")
def index():
    redirect(URL("dashboard"))