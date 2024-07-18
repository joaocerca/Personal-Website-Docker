from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from os import environ, path

# init SQLAlchemy so we can use it later in our models
dbase = SQLAlchemy()

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir,'.env'))

FLASK_APP = environ.get("FLASK_APP")
FLASK_DEBUG = environ.get("FLASK_DEBUG")

# def create_app():
app = Flask(__name__)

app.config['SECRET_KEY'] = environ.get("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_db.sqlite'

dbase.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from .addons.forms import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# blueprint for auth routes in our app
from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

from .backend import backend as backend_blueprint
app.register_blueprint(backend_blueprint)

from .database import database as database_blueprint
app.register_blueprint(database_blueprint)

from .dashboards.musicdashboard import musicdashboard as dashboard_blueprint
app.register_blueprint(dashboard_blueprint)

from .dashboards.musicdashboardgen import musicdashboardgen as dashboard_blueprint
app.register_blueprint(dashboard_blueprint)


    # return app
