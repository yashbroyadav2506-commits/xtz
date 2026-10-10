from app.extensions import db
from app.models import Book, ExchangeRequest


def _login(client, email):
    client.post("/auth/login", data={"email": email, "password": "Password123!"})


def _book(app, owner_id, title="Exchange Book"):
    with app.app_context():
        book = Book(title=title, author="An Author", category="Fiction", condition="Good", owner_id=owner_id)
        db.session.add(book)
        db.session.commit()
        return book.id


def test_request_then_owner_accepts_exchange(client, app, users):
    owner_id, _requester_id = users
    book_id = _book(app, owner_id)
    _login(client, "requester@example.com")
    response = client.post(
        f"/exchanges/books/{book_id}/request",
        data={"message": "I would love to read this"},
        follow_redirects=True,
    )
    assert b"exchange request has been sent" in response.data
    with app.app_context():
        book = db.session.get(Book, book_id)
        exchange = db.session.scalar(db.select(ExchangeRequest).where(ExchangeRequest.book_id == book_id))
        assert book.exchange_status == "Requested"
        assert exchange.status == "Pending"
        exchange_id = exchange.id
    client.post("/auth/logout")
    _login(client, "owner@example.com")
    response = client.post(f"/exchanges/{exchange_id}/accept", follow_redirects=True)
    assert b"Exchange accepted" in response.data
    with app.app_context():
        assert db.session.get(Book, book_id).exchange_status == "Exchanged"
        assert db.session.get(ExchangeRequest, exchange_id).status == "Accepted"


def test_decline_returns_book_to_available_and_duplicate_request_is_blocked(client, app, users):
    owner_id, _requester_id = users
    book_id = _book(app, owner_id)
    _login(client, "requester@example.com")
    client.post(f"/exchanges/books/{book_id}/request", data={"message": ""})
    duplicate = client.post(f"/exchanges/books/{book_id}/request", data={"message": ""}, follow_redirects=True)
    assert b"not currently available" in duplicate.data
    with app.app_context():
        exchange_id = db.session.scalar(db.select(ExchangeRequest.id).where(ExchangeRequest.book_id == book_id))
    client.post("/auth/logout")
    _login(client, "owner@example.com")
    client.post(f"/exchanges/{exchange_id}/decline")
    with app.app_context():
        assert db.session.get(Book, book_id).exchange_status == "Available"
        assert db.session.get(ExchangeRequest, exchange_id).status == "Declined"


def test_non_owner_cannot_accept_incoming_request(client, app, users):
    owner_id, _requester_id = users
    book_id = _book(app, owner_id)
    _login(client, "requester@example.com")
    client.post(f"/exchanges/books/{book_id}/request", data={"message": ""})
    with app.app_context():
        exchange_id = db.session.scalar(db.select(ExchangeRequest.id).where(ExchangeRequest.book_id == book_id))
    assert client.post(f"/exchanges/{exchange_id}/accept").status_code == 403


def test_requester_can_cancel_and_request_again(client, app, users):
    owner_id, _requester_id = users
    book_id = _book(app, owner_id)
    _login(client, "requester@example.com")
    client.post(f"/exchanges/books/{book_id}/request", data={"message": ""})
    with app.app_context():
        first_request_id = db.session.scalar(
            db.select(ExchangeRequest.id).where(ExchangeRequest.book_id == book_id)
        )

    client.post(f"/exchanges/{first_request_id}/cancel")
    with app.app_context():
        assert db.session.get(Book, book_id).exchange_status == "Available"
        assert db.session.get(ExchangeRequest, first_request_id).status == "Cancelled"

    response = client.post(
        f"/exchanges/books/{book_id}/request",
        data={"message": "Still interested"},
        follow_redirects=True,
    )
    assert b"exchange request has been sent" in response.data
    with app.app_context():
        assert db.session.get(Book, book_id).exchange_status == "Requested"
        assert db.session.scalar(
            db.select(ExchangeRequest.id).where(
                ExchangeRequest.book_id == book_id,
                ExchangeRequest.requester_id == users[1],
                ExchangeRequest.status == "Pending",
            )
        ) is not None
