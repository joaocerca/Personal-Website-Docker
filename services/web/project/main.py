from flask import Blueprint, render_template
from flask import current_app
from . import dbase

main = Blueprint('main', __name__, template_folder="templates")

@main.route('/')
def index():
    current_app.logger.info("First contact")
    return render_template("index.html")

