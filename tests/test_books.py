from unittest.mock import patch
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from app.extensions import db
from app.models import Book


def _login(client, email):
    return client.post("/auth/login", data={"email": email, "password": "Password123!"})


def test_owner_can_create_and_edit_book(client, app, users):
    _login(client, "owner@example.com")
    with patch("app.books.routes.lookup_cover_url", return_value="https://covers.openlibrary.org/b/id/123-M.jpg"):
        response = client.post(
            "/books/new",
            data={
                "title": "Test Algorithms",
                "author": "A. Author",
                "category": "Textbook",
                "condition": "Good",
                "description": "A useful book",
                "submit": "Save book",
            },
            follow_redirects=True,
        )
    assert b"Your book has been listed" in response.data
    assert b'Cover of Test Algorithms' in response.data
    with app.app_context():
        book = Book.query.filter_by(title="Test Algorithms").one()
        book_id = book.id
        assert book.cover_url == "https://covers.openlibrary.org/b/id/123-M.jpg"
    response = client.post(
        f"/books/{book_id}/edit",
        data={"title": "Updated Algorithms", "author": "A. Author", "category": "Textbook", "condition": "Good"},
        follow_redirects=True,
    )
    assert b"Your listing has been updated" in response.data


def test_non_owner_cannot_edit_or_delete_book(client, app, users):
    owner_id, _requester_id = users
    with app.app_context():
        book = Book(title="Protected", author="Owner", category="Fiction", condition="Good", owner_id=owner_id)
        db.session.add(book)
        db.session.commit()
        book_id = book.id
    _login(client, "requester@example.com")
    assert client.get(f"/books/{book_id}/edit").status_code == 403
    assert client.post(f"/books/{book_id}/delete").status_code == 403


def test_browse_search_and_filters(client, app, users):
    owner_id, _requester_id = users
    with app.app_context():
        db.session.add(Book(title="The Searchable Book", author="A. Writer", category="Science", condition="New", owner_id=owner_id))
        db.session.commit()
    response = client.get("/?q=Searchable&category=Science&condition=New&status=Available")
    assert response.status_code == 200
    assert b"The Searchable Book" in response.data
    assert b"Book Owner" in response.data


def test_pagination_second_page_loads_and_keeps_filters(client, app, users):
    owner_id, _requester_id = users
    with app.app_context():
        db.session.add_all(
            [
                Book(
                    title=f"Science Book {number:02d}",
                    author="A. Writer",
                    category="Science",
                    condition="Good",
                    owner_id=owner_id,
                )
                for number in range(13)
            ]
        )
        db.session.commit()

    response = client.get("/?category=Science&page=2")
    assert response.status_code == 200
    assert b"Science Book 00" in response.data
    assert b"Internal Server Error" not in response.data

    class PaginationLinks(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                attributes = dict(attrs)
                if "page-link" in attributes.get("class", ""):
                    self.hrefs.append(attributes.get("href", ""))

    links = PaginationLinks()
    links.feed(response.get_data(as_text=True))
    page_one_link = next(href for href in links.hrefs if parse_qs(urlsplit(href).query).get("page") == ["1"])
    assert parse_qs(urlsplit(page_one_link).query)["category"] == ["Science"]


def test_cover_lookup_prefers_exact_title_and_author():
    import json
    from io import BytesIO
    from unittest.mock import patch as mock_patch

    from app.books.covers import lookup_cover_url

    results = {
        "docs": [
            {"title": "The Alchemist Graphic Novel", "author_name": ["Paulo Coelho"], "cover_i": 10},
            {"title": "The Alchemist", "author_name": ["Paulo Coelho"], "cover_i": 20},
        ]
    }
    with mock_patch("app.books.covers.urlopen", return_value=BytesIO(json.dumps(results).encode())):
        cover_url = lookup_cover_url("The Alchemist", "Paulo Coelho")
    assert cover_url == "https://covers.openlibrary.org/b/id/20-M.jpg"
