from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask, g, request
from flask_mail import Mail
from app.constants import FlashMsgType
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel, lazy_gettext as _l
import logging

app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migration engine
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize the login manager and set the login view
login = LoginManager(app)
login.login_view = "login"
login.login_message = _l("Please log in to access this page.")
login.login_message_category = FlashMsgType.DANGER

# Inititialize mail instance
mail = Mail(app)


# Initialize Babel instance - Begin
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, "user", None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(app.config["LANGUAGES"])


def get_timezone():
    user = getattr(g, "user", None)
    if user is not None:
        return user.timezone


babel = Babel(app, locale_selector=get_locale, timezone_selector=get_timezone)
# Initialize Babel instance - End


if not app.debug:
    # Attach mail handler to app logger
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
            auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        secure = None
        if app.config["MAIL_USE_TLS"]:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            fromaddr=app.config["MAIL_ADMINS"][0],
            toaddrs=app.config["MAIL_ADMINS"],
            subject="Microblog Failure",
            credentials=auth,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # Attach file handler to app logger
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        "logs/microblog.log", maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Microblog startup")


# Provide user loader function for Flask-Login
@login.user_loader
def load_user(user_id):
    """Load a user by ID."""
    from app.models import User

    return User.query.get(int(user_id))


# Import routes after creating the app to avoid circular imports
from app import routes, models, errors, cli
