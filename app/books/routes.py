from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.books import bp
from app.books.covers import lookup_cover_url
from app.extensions import db
from app.forms import BookForm, CATEGORIES, CONDITIONS
from app.models import Book, ExchangeRequest


def _owned_book(book_id):
    book = db.get_or_404(Book, book_id)
    if book.owner_id != current_user.id:
        abort(403)
    return book


@bp.get("/")
def index():
    query = db.select(Book).join(Book.owner)
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    condition = request.args.get("condition", "")
    status = request.args.get("status", "")
    sort = request.args.get("sort", "newest")

    if search:
        term = f"%{search}%"
        query = query.where(or_(Book.title.ilike(term), Book.author.ilike(term)))
    if category in CATEGORIES:
        query = query.where(Book.category == category)
    if condition in CONDITIONS:
        query = query.where(Book.condition == condition)
    if status in ("Available", "Requested", "Exchanged"):
        query = query.where(Book.exchange_status == status)
    if sort == "title":
        query = query.order_by(Book.title.asc(), Book.id.asc())
    else:
        sort = "newest"
        query = query.order_by(Book.created_at.desc(), Book.id.desc())

    page = request.args.get("page", 1, type=int)
    books = db.paginate(query, page=max(page, 1), per_page=12, error_out=False)
    pagination_args = request.args.to_dict()
    pagination_args.pop("page", None)
    return render_template(
        "books/index.html",
        books=books,
        categories=CATEGORIES,
        conditions=CONDITIONS,
        filters={"q": search, "category": category, "condition": condition, "status": status, "sort": sort},
        pagination_args=pagination_args,
    )


@bp.get("/books/<int:book_id>")
def detail(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template("books/detail.html", book=book)


@bp.route("/books/new", methods=["GET", "POST"])
@login_required
def create():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            category=form.category.data,
            condition=form.condition.data,
            description=form.description.data.strip() or None,
            owner=current_user,
        )
        db.session.add(book)
        db.session.commit()
        book.cover_url = lookup_cover_url(book.title, book.author)
        db.session.commit()
        flash("Your book has been listed.", "success")
        return redirect(url_for("books.detail", book_id=book.id))
    return render_template("books/form.html", form=form, heading="List a book")


@bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit(book_id):
    book = _owned_book(book_id)
    if book.exchange_status != "Available":
        flash("Only available books can be edited.", "warning")
        return redirect(url_for("books.detail", book_id=book.id))
    form = BookForm(obj=book)
    if form.validate_on_submit():
        cover_changed = (
            book.title.strip() != form.title.data.strip()
            or book.author.strip() != form.author.data.strip()
        )
        form.populate_obj(book)
        book.title = book.title.strip()
        book.author = book.author.strip()
        book.description = (book.description or "").strip() or None
        if cover_changed:
            book.cover_url = lookup_cover_url(book.title, book.author)
        db.session.commit()
        flash("Your listing has been updated.", "success")
        return redirect(url_for("books.detail", book_id=book.id))
    return render_template("books/form.html", form=form, heading="Edit your book")


@bp.post("/books/<int:book_id>/delete")
@login_required
def delete(book_id):
    book = _owned_book(book_id)
    if book.exchange_status != "Available":
        flash("Only available books can be deleted.", "warning")
        return redirect(url_for("books.detail", book_id=book.id))
    db.session.delete(book)
    db.session.commit()
    flash("Your listing has been removed.", "info")
    return redirect(url_for("books.dashboard"))


@bp.get("/dashboard")
@login_required
def dashboard():
    my_books = db.session.scalars(
        db.select(Book).where(Book.owner_id == current_user.id).order_by(Book.created_at.desc())
    ).all()
    incoming = db.session.scalars(
        db.select(ExchangeRequest)
        .join(Book, ExchangeRequest.book_id == Book.id)
        .where(Book.owner_id == current_user.id)
        .order_by(ExchangeRequest.created_at.desc())
    ).all()
    sent = db.session.scalars(
        db.select(ExchangeRequest)
        .where(ExchangeRequest.requester_id == current_user.id)
        .order_by(ExchangeRequest.created_at.desc())
    ).all()
    return render_template("books/dashboard.html", my_books=my_books, incoming=incoming, sent=sent)
