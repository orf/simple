from base64 import b32encode
import functools
import json
import os
from os import urandom
import datetime
from urllib import parse
import mimetypes
import sys

from flask import Flask, render_template, abort, request, Response, redirect, url_for, send_from_directory, \
    make_response, session, g
from flask.ext.basicauth import BasicAuth
from werkzeug.utils import secure_filename
from flask_seasurf import SeaSurf
from pony import orm
from pony.orm import CommitException
import markdown
import requests
from werkzeug.datastructures import FileStorage
from werkzeug.contrib.cache import FileSystemCache

from simple.bing_images import get_latest_header_images
from simple.util import iter_to_stream, Pagination, slugify


if not os.getcwd() in sys.path:
    sys.path.append(os.getcwd())

app = Flask(__name__)
app.config.update(
    PERSONA_JS='https://login.persona.org/include.js',
    PERSONA_VERIFIER='https://verifier.login.persona.org/verify'
    )
app.config.from_object("simple_settings")
app.secret_key = app.config["SECRET_KEY"]

if not app.config["DEBUG"]:
    app.static_folder = os.path.join(os.getcwd(), "static")

db = orm.Database('sqlite',
                  os.path.join(os.getcwd(), app.config["DATABASE_FILE"]), create_db=True)
cache = FileSystemCache(app.config["CACHE_DIR"])
csrf = SeaSurf(app)
basic_auth = BasicAuth(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.jinja_env.globals.update(now=datetime.datetime.now)

md = markdown.Markdown(
    extensions=['fenced_code', 'toc'],
    output_format="html5"
)


class Post(db.Entity):
    _table_ = "posts"
    title = orm.Required(orm.unicode, 100, nullable=False, unique=True)
    slug = orm.Required(orm.unicode, 100, nullable=False, unique=True)

    # Modification dates etc
    created = orm.Required(datetime.date, nullable=False)
    posted = orm.Optional(datetime.datetime, nullable=True)
    modified = orm.Required(datetime.datetime, nullable=True)

    content = orm.Required(orm.unicode, nullable=False)

    header_image = orm.Optional(orm.unicode, nullable=True)
    header_caption = orm.Optional(orm.unicode, nullable=True)

    # Special Page posts
    is_special_page = orm.Required(bool, sql_default=False)

    tags = orm.Set("Tag")

    draft = orm.Required(bool, nullable=False)

    def __repr__(self):
        return "<Post {0}>".format(self.title)

    def created_ago(self):
        return self.created - datetime.date.today()

    def url(self):
        if self.is_special_page:
            return url_for("view_static_page", slug=self.slug)
        return url_for("view_post", slug=self.slug)

    def clear_cache(self):
        cache.delete("post_{0}".format(self.id))

    def rendered_content(self):
        key = "post_{0}".format(self.id)
        hit = cache.get(key)
        if hit:
            return hit

        content = md.convert(self.content)
        cache.set(key, content)
        return content

    def is_local_header_image(self):
        uri = parse.urlparse(self.header_image)
        return not bool(uri.netloc)

    def download_header_image(self):
        req = requests.get(self.header_image, stream=True)
        storage = FileStorage(stream=iter_to_stream(req.iter_content(chunk_size=10)))

        key = str(b32encode(urandom(15)), "utf8")
        ext = mimetypes.guess_extension(req.headers["content-type"])
        name = key + ext
        storage.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
        self.header_image = url_for('uploads', filename=name)


class Tag(db.Entity):
    _table_ = "tags"
    name = orm.Required(orm.unicode, 100)
    post = orm.Required(Post)

    def __repr__(self):
        return "<Tag {0:!r}>".format(self.name)

db.generate_mapping(create_tables=True)


def requires_auth(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        email = session.get('email')
        if email is None or email != app.config["PERSONA_EMAIL"]:
            return redirect(url_for("login_page"))

        return func(*args, **kwargs)

    return _wrapper


@app.route('/')
@orm.db_session
def index():
    special_pages = []
    posts_qs = orm.select(p for p in Post if p.draft is False).order_by(orm.desc(Post.posted))

    try:
        start_page = int(request.args.get("page", 1))
        if start_page < 1: start_page = 1
    except ValueError:
        start_page = 1

    pag = Pagination(start_page, 5, posts_qs.count())
    posts = posts_qs.limit(5, offset=pag.offset)

    return render_template("index.html",
                           posts=posts, paginator=pag,
                           title=app.config["SITE_TITLE"], show_header=True, special_pages=special_pages)


@app.route('/_posts/')
@requires_auth
@orm.db_session
def list_posts():
    return render_template("drafts.html",
                           posts=orm.select(p for p in Post).order_by(orm.desc(Post.modified)),
                           title="Posts")


@app.route("/<string:slug>")
@orm.db_session
def view_post(slug):
    post = orm.select(p for p in Post
                      if p.slug == slug and p.draft is False
                      and p.is_special_page is not True).get()

    if post is None:
        return abort(404)

    return render_template("post.html",
                           post=post)


@app.route("/page/<string:slug>")
@orm.db_session
def view_static_page(slug):
    post = orm.select(p for p in Post if p.slug == slug
                      and p.draft is False
                      and p.is_special_page is True).get()

    if post is None:
        return abort(404)

    return render_template("post.html",
                           post=post)


@app.route("/_header_images", methods=["GET"])
@requires_auth
def header_images():
    # Can only retrieve 19 images, 5 at a max time.
    images = []
    images.extend(get_latest_header_images(0)["images"])
    images.extend(get_latest_header_images(5)["images"])
    images.extend(get_latest_header_images(10)["images"])
    images.extend(get_latest_header_images(15, num=4)["images"])

    return Response(
        json.dumps(
            images
        ), content_type="application/json")


@app.route("/_new", methods=["POST"])
@requires_auth
@orm.db_session
def new_post():
    p = Post(
        title=request.form["title"],
        slug=slugify(request.form["title"]),
        created=datetime.date.today(),
        modified=datetime.datetime.now(),
        content=" ",
        is_special_page=False,
        draft=True
    )

    resp = {"success": False}

    try:
        orm.commit()
    except CommitException:
        resp["error"] = "Title must be unique"
    else:
        resp["success"] = True
        resp["url"] = url_for("view_draft", id=p.id)

    return Response(json.dumps(resp),  mimetype='application/json')


@app.route("/_preview/<int:id>", methods=["GET"])
@requires_auth
@orm.db_session
def preview_post(id):
    post = orm.select(p for p in Post if p.id == id and p.draft is True).get()

    if post is None:
        return abort(404)

    return render_template("post.html",
                           post=post)


@app.route("/_delete/<int:id>", methods=["POST"])
@requires_auth
@orm.db_session
def delete_post(id):
    post = orm.select(p for p in Post if p.id == id).get()
    post.delete()
    orm.commit()

    if "redirect" in request.form:
        return redirect(request.form["redirect"])

    return redirect(url_for('index'))


@app.route("/_publish/<int:id>", methods=["POST"])
@requires_auth
@orm.db_session
def publish_post(id):
    post = orm.select(p for p in Post if p.id == id).get()

    # If the post is newly being published we might need to download the header image
    if post.draft is True:
        # If the URI is a local path then don't do anything, otherwise grab it and make it a local path.
        if not post.is_local_header_image():
            # Download the image and save it
            post.download_header_image()

        post.posted = datetime.datetime.now()

    post.draft = not post.draft
    orm.commit()

    return redirect(url_for('view_draft', id=post.id)) if post.draft \
        else redirect(url_for('view_post', slug=post.slug))


@app.route("/_edit/<int:id>", methods=["POST", "GET"])
@requires_auth
@orm.db_session
def view_draft(id):
    post = orm.select(p for p in Post if p.id == id).get()

    if post is None:
        return abort(404)

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.header_image = request.form["header_image"]
        post.header_caption = request.form["header_caption"]

        if post.draft:
            # Only update the slug if the post is a draft.
            post.slug = slugify(post.title)
        elif not post.is_local_header_image():
            post.download_header_image()  # Possible race condition

        resp = {"success": False}

        try:
            orm.commit()
        except CommitException:
            resp["error"] = "Title must be unique"
        else:
            resp["success"] = True

        post.clear_cache()

        return Response(json.dumps(resp),  mimetype='application/json')

    return render_template("edit_post.html",
                           post=post)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/_upload", methods=["POST"])
@requires_auth
def upload_file():
    file_upload = request.files['file']
    if file_upload and allowed_file(file_upload.filename):
        filename = secure_filename(file_upload.filename)
        key = str(b32encode(urandom(5)), "utf8")

        filename, extension = os.path.splitext(filename)
        filename = filename + '_' + key + extension
        file_upload.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        url = url_for('uploads', filename=filename)
        return Response(json.dumps({'status': 'ok', 'url': url, 'name': filename}),  mimetype='application/json')


@app.route("/posts.rss")
@orm.db_session
def feed():
    rendered = cache.get("rss_feed")
    if rendered is None:
        posts = orm.select(p for p in Post if p.draft is False).order_by(orm.desc(Post.posted)).limit(10)
        rendered = render_template('index.xml', posts=posts)
        cache.set("rss_feed", rendered)

    response = make_response(rendered)
    response.mimetype = "application/xml"
    return response


@app.before_request
def get_current_user():
    g.user = None
    email = session.get('email')
    if email is not None:
        g.user = email

# Shamefully all stolen from the flask persona example.
@app.route('/_login', methods=["GET"])
def login_page():
    email = g.user
    if email == app.config["PERSONA_EMAIL"]:
        return redirect(url_for("list_posts"))

    return render_template("login.html", title="Welcome")


@app.route('/_auth/login', methods=['GET', 'POST'])
def login_handler():
    """This is used by the persona.js file to kick off the
    verification securely from the server side.  If all is okay
    the email address is remembered on the server.
    """
    resp = requests.post(app.config['PERSONA_VERIFIER'], data={
        'assertion': request.form['assertion'],
        'audience': request.host_url,
    }, verify=True)
    if resp.ok:
        verification_data = resp.json()
        if verification_data['status'] == 'okay':
            session['email'] = verification_data['email']
            return 'OK'

    abort(400)


@app.route('/_auth/logout', methods=['POST'])
def logout_handler():
    """This is what persona.js will call to sign the user
    out again.
    """
    session.clear()
    return 'OK'


if __name__ == '__main__':
    app.run(debug=True)
