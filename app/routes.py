from app import app
from flask import render_template, flash, redirect, url_for, request
from app import db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from urllib.parse import urlsplit
import sqlalchemy as sa
from datetime import datetime, timezone


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route("/")
@app.route("/index")
@login_required
def index():

    return render_template(
        "index.html",
        title="Home",
        user=current_user,
        posts=current_user.get_posts(),
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
            flash("Invalid username or password", "error")
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
        # Create user
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # TODO: temp post
        user.posts.add(
            Post(content="First post (Auto generated after registering user)")
        )
        user.posts.add(
            Post(content="Second post (Auto generated after registering user)")
        )

        db.session.add(
            user
        )  # The reason Post object was saved even without explicit session.add(post) or cascade="all" is due to the default save-update cascade behavior of SQLAlchemy relationships. When post3 was assigned to user2.posts, and user2 was added to the session, SQLAlchemy's object graph traversal during the flush detected post3 as a new, related object and automatically included it in the transaction for saving. This automatic behavior is convenient but can sometimes obscure the underlying session management if you're not aware of the default cascade rules.
        db.session.commit()

        flash("Congratulations, you are now a registered user!", "success")
        return redirect(url_for("login"))

    # Render the registration template with the form
    return render_template(
        "register.html",
        title="Register",
        form=form,
    )


@app.route("/user/<username>")
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    return render_template(
        "user.html",
        title="User Info",
        user=user,
        posts=get_posts_of_user(username),
        form=form,
    )


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.fullname = form.fullname.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("edit_profile"))

    if request.method == "GET":
        form.fullname.data = current_user.fullname
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.route("/user/<username>/<action>", methods=["POST"])
@login_required
def user_action(username, action):
    form = EmptyForm()

    if form.validate_on_submit():

        # Case user exists
        user = User.query.filter(User.username == username).first()
        if user is None:
            flash("User not found.", "error")
            return redirect(url_for("index"))

        # Case is current user
        if user == current_user:
            flash("Can not follow/unfollow yourself.", "error")
            return redirect(url_for("user", username=username))

        # Case action invalid
        if action != "follow" and action != "unfollow":
            flash("Action invalid.", "error")
            return redirect(url_for("user", username=username))

        # Case valid
        if action == "follow":
            flash("Follow successfully.", "success")
            current_user.follow(user)
        else:
            flash("Unfollow successfully.", "success")
            current_user.unfollow(user)
        db.session.commit()
        return redirect(url_for("user", username=username))

    return redirect(url_for("index"))


def get_posts_of_user(username):
    user = User.query.filter(User.username == username).first()
    if user is None:
        return []

    posts = Post.query.filter(Post.user_id == user.id).all()
    return posts
