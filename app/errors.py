from app import app, db
from flask import render_template
from sqlalchemy.exc import SQLAlchemyError


@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html"), 404


@app.errorhandler(SQLAlchemyError)
def database_error(err):
    db.session.rollback()
    return render_template("500.html"), 500


@app.errorhandler(500)
def internal_error(err):
    return render_template("500.html"), 500
