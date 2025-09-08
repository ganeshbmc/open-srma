from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json # Import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///srma.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Custom Jinja2 filter to parse JSON
def from_json(value):
    if value:
        return json.loads(value)
    return {}

# Custom Jinja2 filter to convert to JSON
def to_json(value):
    return json.dumps(value)

app.jinja_env.filters['from_json'] = from_json
app.jinja_env.filters['tojson'] = to_json # Add tojson filter

from app import routes, models
