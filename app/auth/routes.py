from app.auth import bp
from flask import render_template, flash, redirect, url_for, request
from app import db
from app.constants import (
    FlashMsgType,
)
from app.auth.email import send_password_reset_email_asyncio
from app.auth.forms import (
    ForgotPasswordForm,
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
)
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from urllib.parse import urlsplit
from flask_babel import _


@bp.route("/login", methods=["GET", "POST"])
def login():

    # Check if the user is already authenticated
    # If so, redirect to the index page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Create a new login form instance
    # and set the custom hidden field value
    form = LoginForm()
    form.custom_hiden_field.data = "hidden_value"

    # Validate the form on submission
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid username or password"), FlashMsgType.DANGER)
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if (
            not next_page or urlsplit(next_page).netloc != ""
        ):  # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
            next_page = url_for("main.index")
        return redirect(next_page)

    # Render the login template with the form
    return render_template(
        "auth/login.html",
        title="Sign In",
        form=form,
    )


@bp.route("/logout")
@login_required
def logout():
    """Log out the user and redirect to the index page."""
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    # Check if the user is already authenticated
    # If so, redirect to the index page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Create a new registration form instance
    form = RegistrationForm()

    # Validate the form on submission
    if form.validate_on_submit():
        # Create user
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        db.session.add(
            user
        )  # The reason Post object was saved even without explicit session.add(post) or cascade="all" is due to the default save-update cascade behavior of SQLAlchemy relationships. When post3 was assigned to user2.posts, and user2 was added to the session, SQLAlchemy's object graph traversal during the flush detected post3 as a new, related object and automatically included it in the transaction for saving. This automatic behavior is convenient but can sometimes obscure the underlying session management if you're not aware of the default cascade rules.
        db.session.commit()

        flash(
            _("Congratulations, you are now a registered user!"), FlashMsgType.SUCCESS
        )
        return redirect(url_for("auth.login"))

    # Render the registration template with the form
    return render_template(
        "auth/register.html",
        title="Register",
        form=form,
    )


@bp.route("/forgot_password", methods=["GET", "POST"])
async def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            await send_password_reset_email_asyncio(user)
        flash(
            _("Reset password mail has been sent. Please check your mailbox"),
            "success",
        )

    return render_template(
        "auth/forgot_password.html", title="Forgot Password", form=form
    )


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user = User.verify_reset_password_token(token)
    if not user:
        flash(
            _("Reset password link is incorrect or has been expired!"),
            FlashMsgType.DANGER,
        )
        return redirect(url_for("main.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_("Change password successfully!"), FlashMsgType.SUCCESS)
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/reset_password.html", title="Reset password", form=form
    )
