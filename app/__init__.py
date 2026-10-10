import click
from flask import Flask, render_template

from config import Config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../public",
        static_url_path="",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import Book, ExchangeRequest, User
    from app.auth import bp as auth_bp
    from app.books import bp as books_bp
    from app.exchanges import bp as exchanges_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(exchanges_bp)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.cli.command("seed")
    def seed():
        """Create three demo users and a set of sample books."""
        demo_users = [
            ("Aarav Sharma", "aarav@example.com"),
            ("Meera Patel", "meera@example.com"),
            ("Kabir Singh", "kabir@example.com"),
        ]
        users = {}
        for name, email in demo_users:
            user = db.session.scalar(db.select(User).filter_by(email=email))
            if user is None:
                user = User(name=name, email=email)
                user.set_password("BookSwap123!")
                db.session.add(user)
            users[email] = user

        db.session.flush()
        samples = [
            ("The Alchemist", "Paulo Coelho", "Literature", "Good", "A journey of purpose and discovery.", "aarav@example.com"),
            ("Pride and Prejudice", "Jane Austen", "Fiction", "Like New", "A beloved classic in excellent shape.", "meera@example.com"),
            ("Introduction to Algorithms", "Thomas H. Cormen", "Textbook", "Fair", "Useful for computer science coursework.", "kabir@example.com"),
            ("Atomic Habits", "James Clear", "Self-Help", "Good", "Practical ideas for building better habits.", "aarav@example.com"),
            ("A Brief History of Time", "Stephen Hawking", "Science", "Like New", "An accessible introduction to cosmology.", "meera@example.com"),
            ("Clean Code", "Robert C. Martin", "Technology", "Good", "Programming craft and maintainability.", "kabir@example.com"),
            ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", "Fair", "Paperback with some shelf wear.", "aarav@example.com"),
            ("Sapiens", "Yuval Noah Harari", "Non-Fiction", "Like New", "A history of humankind.", "meera@example.com"),
            ("Organic Chemistry", "Paula Yurkanis Bruice", "Textbook", "Good", "Notes are limited to a few pages.", "kabir@example.com"),
            ("The Design of Everyday Things", "Don Norman", "Technology", "Good", "Thoughtful book on human-centered design.", "aarav@example.com"),
            ("To Kill a Mockingbird", "Harper Lee", "Literature", "Like New", "A clean copy ready for its next reader.", "meera@example.com"),
            ("The Selfish Gene", "Richard Dawkins", "Science", "Fair", "Well-read copy, all pages intact.", "kabir@example.com"),
            ("Deep Work", "Cal Newport", "Self-Help", "New", "Unused copy.", "aarav@example.com"),
            ("The Art of War", "Sun Tzu", "Other", "Good", "Compact edition with a short introduction.", "meera@example.com"),
            ("Python Crash Course", "Eric Matthes", "Technology", "Like New", "Great for learning Python fundamentals.", "kabir@example.com"),
        ]
        existing_titles = set(db.session.scalars(db.select(Book.title)).all())
        for title, author, category, condition, description, owner_email in samples:
            if title not in existing_titles:
                db.session.add(
                    Book(
                        title=title,
                        author=author,
                        category=category,
                        condition=condition,
                        description=description,
                        owner=users[owner_email],
                    )
                )
        db.session.commit()
        click.echo("Seeded demo users and sample books (password: BookSwap123!).")

    @app.cli.command("refresh-covers")
    @click.option("--all", "refresh_all", is_flag=True, help="Look up covers again, including books with saved covers.")
    def refresh_covers(refresh_all):
        """Look up and cache book covers from Open Library."""
        from app.books.covers import lookup_cover_url

        query = db.select(Book).order_by(Book.id)
        if not refresh_all:
            query = query.where(Book.cover_url.is_(None))
        books = db.session.scalars(query).all()
        found = 0
        for book in books:
            book.cover_url = lookup_cover_url(book.title, book.author)
            found += book.cover_url is not None
            db.session.commit()
            click.echo(f"{'Found cover' if book.cover_url else 'No cover found'}: {book.title}")
        click.echo(f"Checked {len(books)} book(s); cached {found} cover(s).")

    return app
