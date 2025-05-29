from datetime import datetime, timezone
from typing import Optional
from flask import url_for
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app import db
from app import login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


# https://docs.sqlalchemy.org/en/20/orm/join_conditions.html#self-referential-many-to-many-relationship
user_connection = sa.Table(
    "user_connection",
    db.metadata,
    sa.Column("following_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("follower_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    username: orm.Mapped[str] = orm.mapped_column(
        sa.String(80), index=True, unique=True
    )
    email: orm.Mapped[str] = orm.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(256))
    fullname: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(256), index=True)
    last_seen: orm.Mapped[Optional[datetime]] = orm.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    about_me: orm.Mapped[Optional[str]] = orm.mapped_column(sa.String(256))

    # Relationship to Post
    posts: orm.WriteOnlyMapped[list["Post"]] = orm.relationship(
        back_populates="author"
    )  # TODO: check WriteOnlyMapped

    followers: orm.WriteOnlyMapped[list["User"]] = orm.relationship(
        secondary=user_connection,  # This is the junction table
        primaryjoin=id
        == user_connection.c.following_id,  # How the 'left' side (this side's ID) connects to the junction table
        secondaryjoin=id
        == user_connection.c.follower_id,  # How the 'right' side (other side's ID) connects to the junction table
        back_populates="following",
    )

    following: orm.WriteOnlyMapped[list["User"]] = orm.relationship(
        secondary=user_connection,  # configures the association table that is used for this relationship
        primaryjoin=id
        == user_connection.c.follower_id,  # How the 'left' side (this side's ID) connects to the junction table
        secondaryjoin=id
        == user_connection.c.following_id,  # How the 'right' side (other side's ID) connects to the junction table
        back_populates="followers",
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password) -> None:
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_display_name(self):
        return self.fullname or self.username

    def get_avatar_url(self, size):
        digest = md5(
            self.email.lower().encode("utf-8")
        ).hexdigest  # because the MD5 support in Python works on bytes and not on strings -> encode the string as bytes before passing it on to the hash function
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def count_followers(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery()
        )
        return db.session.scalar(query)

    def count_following(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery()
        )
        return db.session.scalar(query)


class Post(db.Model):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    content: orm.Mapped[str] = orm.mapped_column(sa.String(5000))
    timestamp: orm.Mapped[datetime] = orm.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey(User.id), index=True)

    # Relationship to User
    author: orm.Mapped[User] = orm.relationship(back_populates="posts")

    def __repr__(self):
        return f"<Post {self.content}>"

    # Helper method to serialize post to dictionary for JSON response
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),  # ISO 8601 format for easy JS parsing
            "author": {
                "avatar_url": self.author.get_avatar_url(50),
                "user_url": url_for("user", username=self.author.username),
                "display_name": (self.author.get_display_name()),
            },
        }

    @classmethod
    def query_all_posts(cls):
        return sa.select(Post).order_by(Post.timestamp.desc(), Post.id.desc())

    @classmethod
    def query_posts_of_user(cls, user_id):
        # Query - Select posts whose author are user
        return (
            sa.select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.timestamp.desc(), Post.id.desc())
        )

    @classmethod
    def query_posts_of_user_and_following(cls, user_id):
        # Subquery - Select user's following
        subquery_following_ids = (
            sa.select(user_connection.c.following_id)
            .where(user_connection.c.follower_id == user_id)
            .subquery()
        )

        # Query - Select posts whose author are following or user (order: newest)
        return (
            sa.select(Post)
            .where(
                sa.or_(
                    Post.user_id == user_id,
                    -Post.user_id.in_(subquery_following_ids),
                )
            )
            .order_by(Post.timestamp.desc(), Post.id.desc())
        )


class QueryUtility:
    @classmethod
    def pagination_by_keyset(cls, base_query, per_page, cursor_timestamp, cursor_id):

        if cursor_timestamp and cursor_id:
            base_query = base_query.where(
                sa.or_(
                    Post.timestamp < cursor_timestamp,
                    sa.and_(Post.timestamp == cursor_timestamp, Post.id < cursor_id),
                )
            )

        return base_query.limit(per_page)

    @classmethod
    def pagination_by_offset(cls, base_query, per_page, page):
        return base_query.offset((page - 1) * per_page).limit(per_page)

    @classmethod
    def count_total(cls, base_query):
        query = sa.select(sa.func.count()).select_from(base_query.subquery())
        return db.session.scalar(query)
