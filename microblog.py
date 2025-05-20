from app import app
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app import db
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    """Create a shell context for Flask CLI."""
    return {
        "sa": sa,
        "orm": orm,
        "db": db,
        "User": User,
        "Post": Post,
        "init_test_db": init_test_db,
        "test_query": test_query,
    }


def init_test_db():
    """Initialize the test database."""
    db.drop_all()
    db.create_all()
    """Initialize the test database with sample data."""
    user1 = User(username="user1", email="user1@test.com")
    user2 = User(username="user2", email="user2@test.com")
    post1 = Post(body="Hello, world!", author=user1)
    post2 = Post(body="Flask is awesome!", author=user2)

    db.session.add(user1)
    db.session.add(user2)
    db.session.add(post1)
    db.session.add(post2)
    db.session.commit()

    print("Test database initialized with sample data.")


def test_query():
    """Test the query function."""

    # Query all users
    query = sa.select(User).order_by(User.username)
    users = db.session.scalars(query)
    for user in users:
        print(user)

    # Query user1
    query = sa.select(User).filter(User.username == "user1")
    user1 = db.session.scalar(query)
    print(user1)

    # Query user1's posts
    query = user1.posts.select()
    posts = db.session.scalars(query)
    print(posts)
