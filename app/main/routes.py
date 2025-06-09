from app.main import bp
from flask import render_template, flash, redirect, url_for, request
from app import db
from app.constants import (
    NUM_POSTS_PER_PAGE,
    FlashMsgType,
    PaginationType,
    PostSearchCondition,
)
from app.main.forms import (
    EditProfileForm,
    EmptyForm,
    NewPostForm,
)
from flask_login import current_user, login_required
from app.models import User, Post
import sqlalchemy as sa
from flask_babel import _
from langdetect import detect, LangDetectException


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = NewPostForm()

    if form.validate_on_submit():
        try:
            language = detect(form.content.data)
        except LangDetectException:
            language = ""

        post = Post(content=form.content.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_("Create post successully."), FlashMsgType.SUCCESS)
        return redirect(
            url_for("main.index")
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
        translations={"translate": _("Translate")},
    )


@bp.route("/explore")
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
        translations={"translate": _("Translate")},
    )


@bp.route("/user/<username>")
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
        translations={"translate": _("Translate")},
    )


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.fullname = form.fullname.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_("Your changes have been saved."), FlashMsgType.SUCCESS)
        return redirect(url_for("main.edit_profile"))

    if request.method == "GET":
        form.fullname.data = current_user.fullname
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title="Edit Profile", form=form)


@bp.route("/user/<username>/<action>", methods=["POST"])
@login_required
def user_action(username, action):
    form = EmptyForm()

    if form.validate_on_submit():

        # Case user exists
        user = User.query.filter(User.username == username).first()
        if user is None:
            flash(
                _("User %(username)s not found.", username=username),
                FlashMsgType.DANGER,
            )
            return redirect(url_for("main.index"))

        # Case is current user
        if user == current_user:
            flash(_("Can not follow/unfollow yourself."), FlashMsgType.DANGER)
            return redirect(url_for("main.user", username=username))

        # Case action invalid
        if action != "follow" and action != "unfollow":
            flash(_("Action invalid."), FlashMsgType.DANGER)
            return redirect(url_for("main.user", username=username))

        # Case valid
        if action == "follow":
            flash(_("Follow successfully."), FlashMsgType.SUCCESS)
            current_user.follow(user)
        else:
            flash(_("Unfollow successfully."), FlashMsgType.SUCCESS)
            current_user.unfollow(user)
        db.session.commit()
        return redirect(url_for("main.user", username=username))

    return redirect(url_for("main.index"))
