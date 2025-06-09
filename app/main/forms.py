from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length
from flask_babel import lazy_gettext as _l


class EditProfileForm(FlaskForm):
    fullname = StringField(_l("Full name"), validators=[Length(min=0, max=256)])
    about_me = TextAreaField(_l("About me"), validators=[Length(min=0, max=256)])
    submit = SubmitField(_l("Submit"))


class EmptyForm(FlaskForm):
    submit = SubmitField(_l("Submit"))


class NewPostForm(FlaskForm):
    content = TextAreaField("", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField(_l("Post"))
