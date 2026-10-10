from urllib.parse import urljoin, urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from app.auth import bp
from app.extensions import db
from app.forms import LoginForm, RegistrationForm
from app.models import User


def _safe_redirect_target(target):
    if not target:
        return None
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(urljoin(request.host_url, target))
    if test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc:
        return target
    return None


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("books.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to BookSwap! Your account is ready.", "success")
        return redirect(url_for("books.index"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("books.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            db.select(User).where(func.lower(User.email) == form.email.data.strip().lower())
        )
        if user is None or not user.check_password(form.password.data):
            flash("Email or password is incorrect.", "danger")
        else:
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(_safe_redirect_target(request.args.get("next")) or url_for("books.index"))
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been signed out.", "info")
    return redirect(url_for("books.index"))
