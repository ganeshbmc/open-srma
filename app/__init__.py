from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import URL
import json
import os

app = Flask(__name__)
# Use SECRET_KEY from environment in production; fallback for local dev
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secret-key')

# Cookie and URL security settings (configurable via env)
def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

app.config['SESSION_COOKIE_SECURE'] = _env_bool('SESSION_COOKIE_SECURE', True)
app.config['REMEMBER_COOKIE_SECURE'] = app.config['SESSION_COOKIE_SECURE']
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

# Outbound email configuration (optional)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = _env_int('MAIL_PORT', 587)
app.config['MAIL_USE_TLS'] = _env_bool('MAIL_USE_TLS', True)
app.config['MAIL_USE_SSL'] = _env_bool('MAIL_USE_SSL', False)
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_FROM'] = os.environ.get('MAIL_FROM') or app.config['MAIL_USERNAME']
app.config['MAIL_SUPPRESS_SEND'] = _env_bool('MAIL_SUPPRESS_SEND', app.debug or app.testing)

# Database configuration: prefer DATABASE_URL (e.g., Railway Postgres), fallback to SQLite
os.makedirs(app.instance_path, exist_ok=True)
def _resolve_database_url() -> str | None:
    # Primary: explicit DATABASE_URL
    url = os.environ.get('DATABASE_URL') or os.environ.get('RAILWAY_DATABASE_URL') or os.environ.get('POSTGRES_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    # Secondary: construct from PG* env vars if present
    pg_host = os.environ.get('PGHOST')
    pg_db = os.environ.get('PGDATABASE')
    pg_user = os.environ.get('PGUSER')
    pg_pass = os.environ.get('PGPASSWORD')
    pg_port = os.environ.get('PGPORT') or '5432'
    if pg_host and pg_db and pg_user and pg_pass:
        return str(
            URL.create(
                drivername='postgresql+psycopg2',
                username=pg_user,
                password=pg_pass,
                host=pg_host,
                port=int(pg_port) if str(pg_port).isdigit() else None,
                database=pg_db,
            )
        )
    return None

database_url = _resolve_database_url()
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'srma.db')

# Expose DB backend indicator for health checks
app.config['DB_BACKEND'] = (
    'postgresql' if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql') else 'sqlite'
)

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
