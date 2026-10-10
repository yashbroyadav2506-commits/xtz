import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False
        ITEMS_PER_PAGE = 12
        SESSION_COOKIE_SECURE = False

    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def users(app):
    with app.app_context():
        owner = User(name="Book Owner", email="owner@example.com")
        owner.set_password("Password123!")
        requester = User(name="Book Requester", email="requester@example.com")
        requester.set_password("Password123!")
        db.session.add_all([owner, requester])
        db.session.commit()
        return owner.id, requester.id
