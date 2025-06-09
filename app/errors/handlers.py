from app import db
from app.errors import bp
from flask import render_template
from sqlalchemy.exc import SQLAlchemyError


@bp.app_errorhandler(404)
def page_not_found(err):
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(SQLAlchemyError)
def database_error(err):
    db.session.rollback()
    return render_template("errors/500.html"), 500


@bp.app_errorhandler(500)
def internal_error(err):
    return render_template("errors/500.html"), 500
