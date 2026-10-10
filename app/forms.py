from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from app.models import User


CATEGORIES = [
    "Fiction", "Non-Fiction", "Textbook", "Science", "Technology",
    "Literature", "Self-Help", "Other",
]
CONDITIONS = ["New", "Like New", "Good", "Fair", "Poor"]


class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class BookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    author = StringField("Author", validators=[DataRequired(), Length(max=160)])
    category = SelectField("Category", choices=[(item, item) for item in CATEGORIES], validators=[DataRequired()])
    condition = SelectField("Condition", choices=[(item, item) for item in CONDITIONS], validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Save book")


class ExchangeRequestForm(FlaskForm):
    message = TextAreaField("Message to the owner", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Send request")
