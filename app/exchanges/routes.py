from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import update

from app.exchanges import bp
from app.extensions import db
from app.forms import ExchangeRequestForm
from app.models import Book, ExchangeRequest


@bp.post("/books/<int:book_id>/request")
@login_required
def request_exchange(book_id):
    book = db.get_or_404(Book, book_id)
    form = ExchangeRequestForm()
    if not form.validate_on_submit():
        flash("Your exchange request could not be submitted. Please try again.", "danger")
        return redirect(url_for("books.detail", book_id=book.id))
    if book.owner_id == current_user.id:
        abort(403)
    if book.exchange_status != "Available":
        flash("This book is not currently available for exchange.", "warning")
        return redirect(url_for("books.detail", book_id=book.id))
    # The conditional update makes availability a single-winner transition.
    reserved = db.session.execute(
        update(Book)
        .where(Book.id == book.id, Book.exchange_status == "Available")
        .values(exchange_status="Requested")
    )
    if reserved.rowcount != 1:
        db.session.rollback()
        flash("This book is no longer available for exchange.", "warning")
        return redirect(url_for("books.detail", book_id=book.id))

    book.exchange_status = "Requested"
    db.session.add(
        ExchangeRequest(
            book=book,
            requester=current_user,
            message=(form.message.data or "").strip() or None,
        )
    )
    db.session.commit()
    flash("Your exchange request has been sent.", "success")
    return redirect(url_for("books.dashboard"))


@bp.post("/<int:request_id>/<action>")
@login_required
def update_request(request_id, action):
    exchange = db.get_or_404(ExchangeRequest, request_id)
    if action not in ("accept", "decline", "cancel"):
        abort(404)
    if action in ("accept", "decline"):
        if exchange.book.owner_id != current_user.id:
            abort(403)
        if exchange.status != "Pending" or exchange.book.exchange_status != "Requested":
            flash("This request is no longer pending.", "warning")
            return redirect(url_for("books.dashboard"))
        if action == "accept":
            exchange.status = "Accepted"
            exchange.book.exchange_status = "Exchanged"
            flash("Exchange accepted. The book is now marked as exchanged.", "success")
        else:
            exchange.status = "Declined"
            exchange.book.exchange_status = "Available"
            flash("Request declined. The book is available again.", "info")
    else:
        if exchange.requester_id != current_user.id:
            abort(403)
        if exchange.status != "Pending" or exchange.book.exchange_status != "Requested":
            flash("Only a pending request can be cancelled.", "warning")
            return redirect(url_for("books.dashboard"))
        exchange.status = "Cancelled"
        exchange.book.exchange_status = "Available"
        flash("Your request has been cancelled.", "info")
    db.session.commit()
    return redirect(url_for("books.dashboard"))
