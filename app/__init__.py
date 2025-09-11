from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
import json # Import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
# Ensure instance folder exists and store DB there
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'srma.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Login manager for authentication
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Custom Jinja2 filter to parse JSON
def from_json(value):
    if value:
        return json.loads(value)
    return {}

# Custom Jinja2 filter to convert to JSON
def to_json(value):
    return json.dumps(value)

app.jinja_env.filters['from_json'] = from_json
# Use Jinja's built-in `tojson` filter; avoid overriding it

from app import routes, models
# Register CLI commands
from app import cli as _app_cli  # noqa: F401

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        from app.models import User
        return User.query.get(int(user_id))
    except Exception:
        return None
