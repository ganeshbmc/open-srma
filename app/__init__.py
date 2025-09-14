from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from sqlalchemy import event
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'

# Database configuration: prefer DATABASE_URL (e.g., Railway Postgres), fallback to SQLite
os.makedirs(app.instance_path, exist_ok=True)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'srma.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Engine options for SQLite in threaded servers (e.g., gunicorn gthread)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
    opts = app.config['SQLALCHEMY_ENGINE_OPTIONS']
    connect_args = dict(opts.get('connect_args') or {})
    connect_args.setdefault('check_same_thread', False)
    opts['connect_args'] = connect_args
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = opts
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

# SQLite PRAGMAs for better concurrency when applicable
try:
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
        @event.listens_for(db.engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                cursor.close()
            except Exception:
                pass
except Exception:
    # Engine might not be ready in some edge import orders; ignore silently
    pass
