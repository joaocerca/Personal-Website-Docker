from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from . import auth
import os

backend = Blueprint('backend', __name__, template_folder="templates")


@backend.route('/backend')
@login_required
def login():
    return render_template('backend.html')

