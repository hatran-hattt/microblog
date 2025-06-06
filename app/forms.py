from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    HiddenField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.constants import LengthValidation
from app.models import User
from flask_babel import lazy_gettext as _l


class LoginForm(FlaskForm):
    username = StringField(
        _l("Username"),
        validators=[
            DataRequired(),
            Length(
                min=LengthValidation.USER_NAME_MIN_LENGTH,
                max=LengthValidation.USER_NAME_MAX_LENGTH,
            ),
        ],
    )
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember Me"))
    custom_hiden_field = HiddenField("Custom Hidden Field")
    submit = SubmitField(_l("Sign In"))


class RegistrationForm(FlaskForm):
    username = StringField(
        _l("Username"),
        validators=[
            DataRequired(),
            Length(
                min=LengthValidation.USER_NAME_MIN_LENGTH,
                max=LengthValidation.USER_NAME_MAX_LENGTH,
            ),
        ],
    )
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password_confirm = PasswordField(
        _l("Confirm Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Register"))

    def validate_username(self, username):
        """Validate the username field."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l("Please use a different username."))

    def validate_email(self, email):
        """Validate the email field."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l("Please use a different email address."))


class EditProfileForm(FlaskForm):
    fullname = StringField(_l("Full name"), validators=[Length(min=0, max=256)])
    about_me = TextAreaField(_l("About me"), validators=[Length(min=0, max=256)])
    submit = SubmitField(_l("Submit"))


class EmptyForm(FlaskForm):
    submit = SubmitField(_l("Submit"))


class NewPostForm(FlaskForm):
    content = TextAreaField("", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField(_l("Post"))


class ForgotPasswordForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Send reset password mail"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("New password"), validators=[DataRequired()])
    password_confirm = PasswordField(
        _l("Confirm new password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Submit"))
