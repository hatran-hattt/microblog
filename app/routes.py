from app import app
from flask import render_template, flash, redirect, url_for
from app import mockdata
from app.forms import LoginForm


@app.route("/")
@app.route("/index")
def index():

    return render_template(
        "index.html",
        title="Home",
        user=mockdata.user,
        posts=mockdata.posts,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    form.custom_hiden_field.data = "hidden_value"

    if form.validate_on_submit():
        # TODO: Add login logic here
        flash(
            f"Login requested for user {form.username.data}, remember_me={form.remember_me.data}"
        )
        return redirect(url_for("index"))
    return render_template(
        "login.html",
        title="Sign In",
        form=form,
    )
