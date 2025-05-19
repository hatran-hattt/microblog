from app import app
from flask import render_template
from . import mockdata


@app.route("/")
@app.route("/index")
def index():

    return render_template(
        "index.html",
        title="Home",
        user=mockdata.user,
        posts=mockdata.posts,
    )
