from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migration engine
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize the login manager and set the login view
login = LoginManager(app)
login.login_view = "login"
login.login_message_category = "error"


# Provide user loader function for Flask-Login
@login.user_loader
def load_user(user_id):
    """Load a user by ID."""
    from app.models import User

    return User.query.get(int(user_id))


# Import routes after creating the app to avoid circular imports
from app import routes, models
