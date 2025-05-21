from app import app
from flask import render_template, flash, redirect, url_for, request
from app import mockdata, db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from urllib.parse import urlsplit


@app.route("/")
@app.route("/index")
@login_required
def index():

    return render_template(
        "index.html",
        title="Home",
        user=current_user,
        posts=mockdata.posts,
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    # Check if the user is already authenticated
    # If so, redirect to the index page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Create a new login form instance
    # and set the custom hidden field value
    form = LoginForm()
    form.custom_hiden_field.data = "hidden_value"

    # Validate the form on submission
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if (
            not next_page or urlsplit(next_page).netloc != ""
        ):  # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
            next_page = url_for("index")
        return redirect(next_page)

    # Render the login template with the form
    return render_template(
        "login.html",
        title="Sign In",
        form=form,
    )


@app.route("/logout")
@login_required
def logout():
    """Log out the user and redirect to the index page."""
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    # Check if the user is already authenticated
    # If so, redirect to the index page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Create a new registration form instance
    form = RegistrationForm()

    # Validate the form on submission
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))

    # Render the registration template with the form
    return render_template(
        "register.html",
        title="Register",
        form=form,
    )
