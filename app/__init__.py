from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask import Flask, g, request, current_app
from flask_mail import Mail
from app.constants import FlashMsgType
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_babel import Babel, lazy_gettext as _l
import logging


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = _l("Please log in to access this page.")
login.login_message_category = FlashMsgType.DANGER
mail = Mail()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)

    # Register blueprints - Start
    from app.main import bp as bp_main
    from app.api import bp as bp_api
    from app.auth import bp as bp_auth
    from app.errors import bp as bp_errors
    from app.cli import bp as bp_cli

    app.register_blueprint(bp_main, url_prefix="/")
    app.register_blueprint(bp_api, url_prefix="/api")
    app.register_blueprint(bp_auth, url_prefix="/auth")
    app.register_blueprint(bp_errors)
    app.register_blueprint(bp_cli)
    # Register blueprints - End

    # Handle before request
    @app.before_request
    def before_request():
        # Save user's last seen
        if current_user.is_authenticated:
            current_user.last_seen = datetime.now(timezone.utc)
            db.session.commit()

        # Save user's locale
        g.locale = str(get_locale())

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

    return app


# Provide user loader function for Flask-Login
@login.user_loader
def load_user(user_id):
    """Load a user by ID."""
    from app.models import User

    return User.query.get(int(user_id))


def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, "user", None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


def get_timezone():
    user = getattr(g, "user", None)
    if user is not None:
        return user.timezone


# Import routes after creating the app to avoid circular imports
from app import models, cli
