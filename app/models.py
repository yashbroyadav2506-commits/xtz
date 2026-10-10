from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    books = db.relationship("Book", back_populates="owner", cascade="all, delete-orphan")
    requests = db.relationship("ExchangeRequest", back_populates="requester", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "category IN ('Fiction', 'Non-Fiction', 'Textbook', 'Science', "
            "'Technology', 'Literature', 'Self-Help', 'Other')",
            name="ck_books_category",
        ),
        CheckConstraint(
            "condition IN ('New', 'Like New', 'Good', 'Fair', 'Poor')",
            name="ck_books_condition",
        ),
        CheckConstraint(
            "exchange_status IN ('Available', 'Requested', 'Exchanged')",
            name="ck_books_exchange_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(160), nullable=False, index=True)
    category = db.Column(db.String(40), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    cover_url = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    exchange_status = db.Column(db.String(20), nullable=False, default="Available", index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    owner = db.relationship("User", back_populates="books")
    exchange_requests = db.relationship("ExchangeRequest", back_populates="book", cascade="all, delete-orphan")


class ExchangeRequest(db.Model):
    __tablename__ = "exchange_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Accepted', 'Declined', 'Cancelled')",
            name="ck_exchange_requests_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    book = db.relationship("Book", back_populates="exchange_requests")
    requester = db.relationship("User", back_populates="requests")


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
