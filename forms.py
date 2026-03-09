from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField

"""
    Contains the Flask Forms to be used for the website.
    
    By: Davin Rousseau
    Date: February 28, 2026
"""

class RegisterForm(FlaskForm):
    """
    Form for registering new users.
    """
    email = StringField("Email", validators=[DataRequired(), Email(message="Not a Valid Email")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters long")])
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    """
    Form for logging users into the website.
    """
    email = StringField("Email", validators=[DataRequired(), Email(message="Not a Valid Email")])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class CreatePostForm(FlaskForm):
    """
    Form for creating a new blog post.
    """
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    """
    Form for submitting comments on blog posts.
    """
    comment_body = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class ContactForm(FlaskForm):
    """
    Form for contacting the admin (main) user
    """
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email Address", validators=[DataRequired(), Email(message="Not a Valid Email")])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, message="Phone number must have at least 10 digits")])
    message = CKEditorField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")