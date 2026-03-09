import os
import smtplib
from dotenv import load_dotenv
from datetime import date
from functools import wraps
from bs4 import BeautifulSoup
from forms import RegisterForm, LoginForm, CreatePostForm, CommentForm, ContactForm
from flask import Flask, render_template, redirect, url_for, abort, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_ckeditor.utils import cleanify
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

"""
    A blog website where users can sign up and leave comments on the blog posts made by me!
        - Using Python/Flask and SQLite/SQLAlchemy.
    
    By: Davin Rousseau
    Date: February 28 - March 4, 2026
"""

# GET CSRF/SECRET KEY FROM ENV FILE
load_dotenv("../../../programming-env-variables/.env")


# GET ETHEREAL EMAIL CREDENTIALS
MY_ETHEREAL_EMAIL = os.getenv("ETHEREAL-EMAIL")
MY_ETHEREAL_PASSWORD = os.getenv("ETHEREAL-PASSWORD")


# CREATE FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("BLOG-CSRF-SECRET-KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)


# CREATE USER LOGIN MANAGEMENT
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """
    Loads/Returns a user into the current site session using the user's ID in the database.

    :param user_id: ID of the user in the database
    :return: User Object, which will be loaded into the current session
    """
    return db.session.get(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE DATABASE TABLES
class User(db.Model, UserMixin):
    """
    Model Representation of a User in the users table in the database, as well as a User for Flask User Login Management.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    username: Mapped[str] = mapped_column(String(250), nullable=False)

    blog_posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    """
    Model Representation of a Blog Post from the blog_posts table in the database for storing the blog posts.
    """
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    author = relationship("User", back_populates="blog_posts")
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    """
    Model Representation of a Comment Record from the comments table in the database for storing comments made for blog posts.
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)

    comment_author = relationship("User", back_populates="comments")
    parent_post = relationship("BlogPost", back_populates="comments")

with app.app_context():
    db.create_all()


# DECORATORS
def admin_only(func_route):
    """
    Decorator that makes a function/route accessible only to the admin user (me) on the website.

    :param func_route: Function/Route to be accessible only to the admin user
    :return: Decorated Function/Route
    """
    @wraps(func_route)
    def decorated_func_route(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return func_route(*args, **kwargs)
        else:
            return abort(403)

    return decorated_func_route


# APP ROUTES
@app.route('/')
def home():
    """
    Returns the home page which shows all blog posts.
    :return: Home page
    """
    all_posts = db.session.execute(db.select(BlogPost)).scalars().all()

    return render_template("index.html", all_posts=all_posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    """
    Returns the registration page. When a new user registers, logs the user in and redirects back to the home page.

    :return: Registration page. Redirect to Home page when a new user registers
    """
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data

        # Check if the user/email already exists in the database and redirect the user to the login page instead
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        if user:
            flash("User with this email already exists, log in instead!", category="error")
            return redirect(url_for('login'))

        password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        username = form.username.data

        new_user = User(
            email=email,
            password=password,
            username=username
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for('home'))

    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """
    Returns the login page. When a user logs in, redirects back to the home page.

    :return: Login page. Redirect to Home page when a user logs in
    """
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        if not user:
            flash("Email not associated with a user, Please try again or register for a new account", category="error")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Incorrect Password, Please try again", category="error")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    """
    Logs out the user from the current session and redirects back to the home page.

    :return: Redirect to Home page
    """
    logout_user()

    return redirect(url_for('home'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    """
    - Returns the page showing the specified blog post and allows for logged-in users to comment on the post.
    - If a user is not logged in and tries to comment on a post, redirects to the login page to encourage them to log in first.

    :param post_id: ID of the blog post in the database
    :return: Page with specified blog post. Redirect to Login page if a user tries to comment without being logged in
    """
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please login or register for a new account to comment on posts")
            return redirect(url_for('login'))

        new_comment = Comment(
            author_id=current_user.id,
            post_id=post_id,
            text=cleanify(form.comment_body.data)
        )
        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", post=requested_post, form=form, comments=requested_post.comments)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    """
    Returns the page for adding a new blog post. If a new post is submitted, redirects back to the home page.
    The admin user is the only user who can add new posts.

    :return: Page for adding a new blog post. Redirect to Home page when a new post is submitted
    """
    form = CreatePostForm()

    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=cleanify(form.body.data),
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    """
    - Returns the same page for adding a new post, but pre-populates the fields with the selected post details so that it can be edited.
    - When a post has been edited, redirects back to the post page.
    - The admin user (me) is the only user who can edit posts.

    :param post_id: ID of the post in the database
    :return: Pre-populated Make Post page for editing. Redirect to the Post page when a post has been edited
    """
    post = db.get_or_404(BlogPost, post_id)

    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )

    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = cleanify(edit_form.body.data)

        db.session.commit()

        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    """
    - Deletes a post from the website/database, then redirects back to the home page.
    - The admin user (me) is the only user who can delete posts.

    :param post_id: ID of the post in the database
    :return: Redirect back to the home page
    """
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/about")
def about():
    """
    Returns the about page.

    :return: About page
    """
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """
    Returns the contact page and sends an email to the admin user (me) when a user sends a message.

    :return: Contact page
    """
    form = ContactForm()

    if form.validate_on_submit():
        name = form.name.data
        email_address = form.email.data
        phone_number = form.phone_number.data
        message_data = cleanify(form.message.data)

        # Use BeautifulSoup to remove HTML tags from the message that's returned from the CKEditor
        soup = BeautifulSoup(message_data, "html.parser")
        message = soup.get_text(separator="\n")

        with smtplib.SMTP("smtp.ethereal.email", port=587) as connection:
            connection.starttls()
            connection.login(user=MY_ETHEREAL_EMAIL, password=MY_ETHEREAL_PASSWORD)
            connection.sendmail(
                from_addr=email_address,
                to_addrs=MY_ETHEREAL_EMAIL,
                msg=f"Subject: New Contact Message sent from Blogs Site User!\n\n"
                    f"From: {name}\nEmail: {email_address}\nPhone Number: {phone_number}\n\nMessage:\n{message}"
            )

        flash("Email sent successfully!")
        return redirect(url_for("contact"))

    return render_template("contact.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
