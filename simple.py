""" simple """

# python imports
import re
import datetime
import os
import time
from functools import wraps
from unicodedata import normalize
from os import urandom
from base64 import b32encode
from email import utils
# web stuff and markdown imports
import markdown
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.security import check_password_hash
from flask import render_template, request, Flask, flash, redirect, url_for, \
    abort, jsonify, Response, make_response
from werkzeug.contrib.cache import FileSystemCache, NullCache
from werkzeug.utils import secure_filename
import json
from flask import send_from_directory

try:
    import pygments
    from pygments.formatters import HtmlFormatter
except ImportError:
    pygments = None

app = Flask(__name__)
app.config.from_object('settings')
app.secret_key = app.config["SECRET_KEY"]

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['USE_FAVICON'] =  os.path.exists(os.path.join(app.static_folder, "favicon.ico"))


db = SQLAlchemy(app)
cache_directory = os.path.dirname(__file__)
try:
    cache = FileSystemCache(os.path.join(cache_directory, "cache"))
except Exception, e:
    print "Could not create cache folder, caching will be disabled."
    print "Error: %s" % e
    cache = NullCache()

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

extensions = ['fenced_code', 'toc']
if pygments is not None:
    extensions.append('codehilite')

MARKDOWN_PARSER = markdown.Markdown(extensions=extensions,
                                    output_format="html5")

if not app.debug:
    import logging
    if not os.path.exists("logs"):
        os.mkdir("logs")
    app.logger.log(logging.INFO,
                   "Logging exceptions to %s" % os.path.join(os.getcwd(),
                                                             'logs/flask.log'))

    file_handler = logging.FileHandler('logs/flask.log')
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)


class Post(db.Model):
    def __init__(self, title=None, created_at=None):
        if title:
            self.title = title
            self.slug = slugify(title)
        if created_at:
            self.created_at = created_at
            self.updated_at = created_at

    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    slug = db.Column(db.String(), unique=True)
    text = db.Column(db.String(), default="")
    draft = db.Column(db.Boolean(), index=True, default=True)
    views = db.Column(db.Integer(), default=0)
    created_at = db.Column(db.DateTime, index=True)
    updated_at = db.Column(db.DateTime)

    def render_content(self):
        _cached = cache.get("post_%s" % self.id)
        if _cached is not None:
            return _cached
        text = MARKDOWN_PARSER.convert(self.text)
        cache.set("post_%s" % self.id, text)
        return text

    def set_content(self, content):
        cache.delete("post_%s" % self.id)
        cache.delete("rss_feed")

        self.text = content

    def get_content(self):
        return self.text


try:
    db.create_all()
except Exception:
    pass

def is_admin():
    auth = request.authorization
    if not auth or not (auth.username == app.config["ADMIN_USERNAME"]
                        and check_password_hash(app.config["ADMIN_PASSWORD"], auth.password)):
        return False
    return True


def requires_authentication(func):
    """ function decorator for handling authentication """
    @wraps(func)
    def _auth_decorator(*args, **kwargs):
        """ does the wrapping """
        if not is_admin():
            return Response("Could not authenticate you", 
                            401, 
                            {"WWW-Authenticate": 'Basic realm="Login Required"'})
        return func(*args, **kwargs)

    return _auth_decorator


@app.route("/")
def index():
    """ Index Page. Here is where the magic starts """
    page = request.args.get("page", 0, type=int)
    posts_master = db.session.query(Post)\
        .filter_by(draft=False).order_by(Post.created_at.desc())
    
    posts_count = posts_master.count()

    posts = posts_master\
        .limit(app.config["POSTS_PER_PAGE"])\
        .offset(page * int(app.config["POSTS_PER_PAGE"])) .all()

    # Sorry for the verbose names, but this seemed like a sensible
    # thing to do.
    last_possible_post_on_page = page * app.config["POSTS_PER_PAGE"] + \
                                 app.config["POSTS_PER_PAGE"]
    there_is_more = posts_count > last_possible_post_on_page

    return render_template("index.html", 
                           posts=posts,
                           now=datetime.datetime.now(),
                           is_more=there_is_more, 
                           current_page=page, 
                           is_admin=is_admin())

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', now=datetime.datetime.now(), is_admin=is_admin()), 404
    
@app.errorhandler(500)
def page_error(e):
    return render_template('500.html', now=datetime.datetime.now(), is_admin=is_admin()), 500

@app.route("/<int:post_id>")
def view_post(post_id):
    """ view_post renders a post and returns the Response object """
    
    try:
        post = db.session.query(Post).filter_by(id=post_id, draft=False).one()
    except NoResultFound:
        abort(404)
    
    return render_template("view.html", post=post, is_admin=is_admin(), preview=False)


@app.route("/<slug>")
def view_post_slug(slug):
    
    try:
        post = db.session.query(Post).filter_by(slug=slug, draft=False).one()
    except NoResultFound:
        abort(404)
        
    pid = request.args.get("pid", "0")
    return render_template("view.html", post=post, pid=pid, is_admin=is_admin(), preview=False)


@app.route("/new", methods=["POST", "GET"])
@requires_authentication
def new_post():
    post = Post(title=request.form.get("title", "untitled"),
                created_at=datetime.datetime.now())

    db.session.add(post)
    db.session.commit()

    return redirect(url_for("edit", post_id=post.id))


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@requires_authentication
def edit(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id).one()
    except NoResultFound:
        abort(404)

    if request.method == "GET":
        return render_template("edit.html", post=post)
    else:
        if post.title != request.form.get("post_title", ""):
            post.title = request.form.get("post_title", "")
            # If the post has been published already then don't update the slug
            if post.draft:
                post.slug = slugify(post.title)

        post.set_content(request.form.get("post_content", ""))
        post.updated_at = datetime.datetime.now()

        if any(request.form.getlist("post_draft", type=int)):
            post.draft = True
        else:
            if post.draft:
                post.draft = False
                post.created_at = datetime.datetime.now()
                post.updated_at = datetime.datetime.now()

        db.session.add(post)
        db.session.commit()
        return redirect(url_for("edit", post_id=post_id))


@app.route("/delete/<int:post_id>", methods=["GET", "POST"])
@requires_authentication
def delete(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id).one()
    except Exception:
        # TODO: define better exceptions for db failure.
        flash("Error deleting post ID %s" % post_id, category="error")
    else:
        db.session.delete(post)
        db.session.commit()

    cache.delete("rss_feed")

    return redirect(request.args.get("next", "")
                    or request.referrer or url_for('index'))


@app.route("/admin", methods=["GET", "POST"])
@requires_authentication
def admin():
    drafts = db.session.query(Post)\
        .filter_by(draft=True).order_by(Post.created_at.desc()).all()
    posts = db.session.query(Post).filter_by(draft=False)\
        .order_by(Post.created_at.desc()).all()
    return render_template("admin.html", drafts=drafts, posts=posts)


@app.route("/admin/save/<int:post_id>", methods=["POST"])
@requires_authentication
def save_post(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id).one()
    except NoResultFound:
        abort(404)
        
    if post.title != request.form.get("title", ""):
        post.title = request.form.get("title", "")
        post.slug = slugify(post.title)
    content = request.form.get("content", "")
    content_changed = content != post.get_content()

    post.set_content(content)
    post.updated_at = datetime.datetime.now()
    db.session.add(post)
    db.session.commit()
    return jsonify(success=True, update=content_changed)


@app.route("/preview/<int:post_id>")
@requires_authentication
def preview(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id).one()
    except NoResultFound:
        return abort(404)

    return render_template("view.html", post=post, preview=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
@requires_authentication
def upload_file():
    if request.method == 'POST':
        file_upload = request.files['file']
        if file and allowed_file(file_upload.filename):
            filename = secure_filename(file_upload.filename)
            key = b32encode(urandom(5))
            filename, extension = os.path.splitext(filename)
            filename = filename + '_' + key + extension
            file_upload.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            url = url_for('uploaded_file', filename=filename)
            return json.dumps({'status': 'ok', 'url': url, 'name': filename})
    return 'ok'
            

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    resp = send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
    dt = datetime.datetime.now() + datetime.timedelta(days=30)
    resp.headers["Expires"] = utils.formatdate(
        time.mktime(dt.timetuple())
    )
    return resp


@app.route("/posts.rss")
def feed():
    rendered = cache.get("rss_feed")
    if rendered is None:
        posts = db.session.query(Post)\
            .filter_by(draft=False)\
            .order_by(Post.created_at.desc())\
            .limit(10).all()
        rendered = render_template('index.xml', posts=posts)
        cache.set("rss_feed", rendered)

    response = make_response(rendered)
    response.mimetype = "application/xml"
    return response


def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word))
        if word:
            result.append(word)
    slug = delim.join(result)
    # This could have issues if a post is marked as draft, then live, then 
    # draft, then live and there are > 1 posts with the same slug. Oh well.
    count = db.session.query(Post).filter_by(slug=slug).count()
    if count > 0:
        return "%s%s%s" % (slug, delim, count)
    else:
        return slug

if __name__ == "__main__":
    if pygments is not None:
        to_write_path = os.path.join(app.static_folder, "css", "code_styles.css")
        if not os.path.exists(to_write_path):
            to_write = HtmlFormatter().get_style_defs(".codehilite")
            try:
                with open(to_write_path, "w") as fd:
                    fd.write(to_write)
            except IOError:
                pass

    app.run(host="0.0.0.0")
