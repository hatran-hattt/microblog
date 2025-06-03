import math
from app import app
from flask import render_template, flash, redirect, url_for, request, jsonify
from app import db
from app.constants import NUM_POSTS_PER_PAGE, PaginationType, PostSearchCondition
from app.email import send_password_reset_email_asyncio
from app.forms import (
    ForgotPasswordForm,
    LoginForm,
    RegistrationForm,
    EditProfileForm,
    EmptyForm,
    NewPostForm,
    ResetPasswordForm,
)
from flask_login import current_user, login_user, logout_user, login_required
from app.models import QueryUtility, User, Post
from urllib.parse import urlsplit
import sqlalchemy as sa
from datetime import datetime, timezone


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = NewPostForm()

    if form.validate_on_submit():
        post = Post(content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Create post successully.", "success")
        return redirect(
            url_for("index")
        )  # Post/Redirect/Get trich (avoids inserting duplicate posts when a user inadvertently refreshes the page after submitting a web form.)

    return render_template(
        "index.html",
        title="Home",
        user=current_user,
        form=form,
        fetch_data_info={
            "per_page": NUM_POSTS_PER_PAGE,
            "search_condition": PostSearchCondition.CURRENT_USER_AND_FOLLOWING,
            "pagination_type": PaginationType.OFFSET,
        },
    )


@app.route("/explore")
@login_required
def explore():

    return render_template(
        "index.html",
        title="Explore",
        user=current_user,
        fetch_data_info={
            "per_page": NUM_POSTS_PER_PAGE,
            "search_condition": PostSearchCondition.ALL,
            "pagination_type": PaginationType.KEYSET,
        },
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
        form=form,
        fetch_data_info={
            "per_page": NUM_POSTS_PER_PAGE,
            "search_condition": PostSearchCondition.USER,
            "pagination_type": PaginationType.KEYSET,
        },
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


@app.route("/forgot_password", methods=["GET", "POST"])
async def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            await send_password_reset_email_asyncio(user)
        flash(
            "Reset password mail has been sent. Please check your mailbox ", "success"
        )

    return render_template("forgot_password.html", title="Forgot Password", form=form)


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user = User.verify_reset_password_token(token)
    if not user:
        flash("Reset password link is incorrect or has been expired!", "error")
        return redirect(url_for("index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Change password successfully!", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", title="Reset password", form=form)


@app.route("/api/posts")
@login_required
def api_posts():

    # Input
    search_condition = request.args.get("search_condition", PostSearchCondition.ALL)
    pagination_type = request.args.get("pagination_type", PaginationType.OFFSET)
    flag_pagination_info = request.args.get("flag_pagination_info", True, type=bool)
    per_page = request.args.get("per_page", NUM_POSTS_PER_PAGE, type=int)
    user_id = request.args.get("user_id")

    # Output
    serialized_posts = None
    pagination_info = {
        # keyset
        "has_more": None,
        "next_cursor": None,
        # offset
        "total_records": None,
        "total_page": None,
    }

    # Get base query
    match search_condition:
        case PostSearchCondition.ALL:
            base_query = Post.query_all_posts()
        case PostSearchCondition.CURRENT_USER_AND_FOLLOWING:
            base_query = Post.query_posts_of_user_and_following(current_user.id)
        case PostSearchCondition.USER:
            if not user_id:
                return jsonify({"error": "Query param 'user_id' is missing"}), 400
            base_query = Post.query_posts_of_user(user_id)
        case _:
            return jsonify({"error": "Invalid query type"}), 400

    # Pagination approach
    match pagination_type:
        case PaginationType.OFFSET:
            # Input
            page = request.args.get("page", 1, type=int)  # TODO test case not number

            # Get pagination query (by offset)
            query = QueryUtility.pagination_by_offset(base_query, per_page, page)

            # Execute query
            posts = db.session.scalars(query).all()

            # Serialize posts to dictionaries
            serialized_posts = [p.to_dict() for p in posts]

            if flag_pagination_info:
                total_records = QueryUtility.count_total(base_query)
                pagination_info["total_records"] = total_records
                pagination_info["total_page"] = math.ceil(total_records / per_page)
        case PaginationType.KEYSET:
            # Check input
            cursor_timestamp_str = request.args.get("cursor_timestamp")
            cursor_id = request.args.get("cursor_id")
            cursor_timestamp = None
            if cursor_timestamp_str:
                try:
                    cursor_timestamp = datetime.fromisoformat(cursor_timestamp_str)
                except ValueError:
                    return jsonify({"error": "Invalid timestamp format"}), 400

            # Get pagination query (by keyset)
            query = QueryUtility.pagination_by_keyset(
                base_query, per_page + 1, cursor_timestamp, cursor_id
            )

            # Execute query
            posts = db.session.scalars(query).all()

            # Check next cursor
            pagination_info["has_more"] = len(posts) > per_page
            if pagination_info["has_more"]:
                pagination_info["next_cursor"] = {
                    "cursor_timestamp": posts[per_page - 1].timestamp.isoformat(),
                    "cursor_id": posts[per_page - 1].id,
                }

            # Serialize posts to dictionaries
            posts_to_return = posts[:per_page]
            serialized_posts = [p.to_dict() for p in posts_to_return]
        case _:
            return jsonify({"error": "Invalid pagination type"}), 400

    return jsonify(
        {
            "posts": serialized_posts,
            "pagination_info": pagination_info if flag_pagination_info else None,
        }
    )
