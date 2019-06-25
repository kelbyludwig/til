import datetime
import config
import hashlib
import binascii
from functools import wraps
from flask import Flask, Response, render_template, request, redirect, url_for
from hmac import compare_digest as compare
from flask_sqlalchemy import SQLAlchemy

# app globals
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLITE_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# helper
def render(template, **kw):
    kw["blog_name"] = config.BLOG_NAME
    return render_template(template, **kw)


def hash_password(password):
    """Returns a ASCII hex password hash using PBKDF2 configuration.
    """
    password = password.encode("utf-8")
    h = hashlib.pbkdf2_hmac("sha256", password, config.SALT, config.ITERATIONS)
    return binascii.hexlify(h)


def credentials_valid(username, password):
    """Returns a boolean indicating if the submitted credentials are valid.
    """
    pw_hash = hash_password(password)
    username_valid = compare(username, config.USERNAME)
    password_valid = compare(pw_hash, config.PASSWORD_HASH)
    return username_valid & password_valid


def authentication_prompt():
    """Prompts for HTTP Basic Auth
    """
    return Response(
        "please submit credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def auth(f):
    """A decorator to add HTTP Basic Auth to routes.

    If the user has configured a None username, no authentication is required.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        creds = request.authorization
        if config.USERNAME is None:
            return f(*args, **kwargs)
        if not creds or not credentials_valid(creds.username, creds.password):
            return authentication_prompt()
        return f(*args, **kwargs)

    return decorated


# models
class Post(db.Model):
    """The content of a TIL blog post.
    """

    id = db.Column(db.Integer, db.Sequence("post_id_seq"), primary_key=True)
    text = db.Column(db.Text, unique=False, nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @staticmethod
    def all():
        """Return all `Post`s with `Tag`s.
        """
        posts = db.session.query(Post).order_by(Post.created.desc()).all()
        for post in posts:
            post._add_tags()
        return posts

    @staticmethod
    def create(text, tag_string):
        """Create a Post and related data.
        """
        post = Post(text=text)
        db.session.add(post)
        db.session.flush()
        tags = Tag.from_string(tag_string)
        for tag in tags:
            post_tag = PostTag(post=post.id, tag=tag.id)
            db.session.add(post_tag)
        db.session.flush()

    def _add_tags(self):
        """Associate array of `Tag`s with `Post`.
        """
        self.tags = (
            db.session.query(Tag).join(PostTag).filter(PostTag.post == self.id).all()
        )


class Tag(db.Model):
    """A subject associated with one or more `Post`s.
    """

    id = db.Column(db.Integer, db.Sequence("tag_id_seq"), primary_key=True)
    text = db.Column(db.Text, unique=True, nullable=False)

    @staticmethod
    def existing(text):
        """Returns an existing `Tag` if it exists.
        """
        return db.session.query(Tag).filter(Tag.text == text).one_or_none()

    @staticmethod
    def from_string(tag_string):
        """Returns (new or existing) `Tag`s given a space-delimited string.
        """
        tags = []
        for text in tag_string.split(" "):
            # ignore empty tags
            if not text.strip():
                continue
            existing_tag = Tag.existing(text)
            if existing_tag:
                tags.append(existing_tag)
            else:
                tag = Tag(text=text)
                db.session.add(tag)
                tags.append(tag)
        db.session.flush()
        return tags


class PostTag(db.Model):
    """Holds the one-to-many `Post` to `Tag`s relationship.
    """

    id = db.Column(db.Integer, db.Sequence("post_tag_id_seq"), primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey(Post.id), nullable=False)
    tag = db.Column(db.Integer, db.ForeignKey(Tag.id), nullable=False)


# routes
@app.route("/", methods=["GET"])
@auth
def index():
    """list all existing `Post`s.
    """
    posts = Post.all()
    return render("index.html", posts=posts)


@app.route("/", methods=["POST"])
@auth
def create():
    """create a new `Post`.
    """
    text = request.form["text"]
    tags = request.form["tags"]
    Post.create(text=text, tag_string=tags)
    db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print("initializing sqlite")
        db.create_all()
        with open("README.md", "r") as rf:
            Post.create(text=rf.read(), tag_string="blogging")
            db.session.commit()
    if len(sys.argv) == 2:
        print("password hash:")
        password = sys.argv[1]
        print(hash_password(password))
