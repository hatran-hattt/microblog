import os

from dotenv import load_dotenv

# main directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# load environment variables from .env
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    MAIL_ADMINS = os.environ.get("MAIL_ADMINS").split(",")

    LANGUAGES = {"en": "English", "vi": "Tiếng Việt"}

    # Google Clould Translation
    GOOGLE_CLOUD_TRANS_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_TRANS_PROJECT_ID")
