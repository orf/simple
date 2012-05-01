from functools import wraps
from flask import render_template, request, Flask, flash, redirect, url_for, abort, jsonify, Response, make_response
import re
from unicodedata import normalize
from flask.ext.sqlalchemy import SQLAlchemy
import datetime
import markdown
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config.from_object('settings')
db = SQLAlchemy(app)

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

class Post(db.Model):
    __tablename__ = "posts"
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    slug  = db.Column(db.String(), unique=True)
    text  = db.Column(db.String(), default="")
    draft = db.Column(db.Boolean(), index=True, default=True)
    views = db.Column(db.Integer(), default=0)
    created_at = db.Column(db.DateTime, index=True)
    updated_at = db.Column(db.DateTime)

    def render_content(self):
        return markdown.Markdown(extensions=['fenced_code'], output_format="html5", safe_mode=True).convert(self.text)

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

def requires_authentication(f):
    @wraps(f)
    def _auth_decorator(*args, **kwargs):
        if not is_admin():
            return Response("Could not authenticate you", 401, {"WWW-Authenticate":'Basic realm="Login Required"'})
        return f(*args, **kwargs)

    return _auth_decorator

@app.route("/")
def index():
    page = request.args.get("page", 0, type=int)
    posts_master = db.session.query(Post).filter_by(draft=False).order_by(Post.created_at.desc())
    posts_count = posts_master.count()

    posts = posts_master.limit(app.config["POSTS_PER_PAGE"]).offset(page*app.config["POSTS_PER_PAGE"]).all()
    is_more = posts_count > ((page*app.config["POSTS_PER_PAGE"]) + app.config["POSTS_PER_PAGE"])

    return render_template("index.html", posts=posts, now=datetime.datetime.now(),
                                         is_more=is_more, current_page=page, is_admin=is_admin())

@app.route("/<int:post_id>")
def view_post(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id, draft=False).one()
    except Exception:
        return abort(404)

    db.session.query(Post).filter_by(id=post_id).update({Post.views:Post.views+1})
    db.session.commit()

    return render_template("view.html", post=post, is_admin=is_admin())

@app.route("/<slug>")
def view_post_slug(slug):
    try:
        post = db.session.query(Post).filter_by(slug=slug,draft=False).one()
    except Exception:
        return abort(404)

    if not any(botname in request.user_agent.string for botname in ['Googlebot','Slurp','Twiceler','msnbot',
                                                                    'KaloogaBot','YodaoBot','"Baiduspider',
                                                                    'googlebot','Speedy Spider','DotBot']):
        db.session.query(Post).filter_by(slug=slug).update({Post.views:Post.views+1})
        db.session.commit()

    pid = request.args.get("pid", "0")
    return render_template("view.html", post=post, pid=pid, is_admin=is_admin())

@app.route("/new", methods=["POST", "GET"])
@requires_authentication
def new_post():
    post = Post()
    post.title = request.form.get("title","untitled")
    post.slug = slugify(post.title)
    post.created_at = datetime.datetime.now()
    post.updated_at = datetime.datetime.now()

    db.session.add(post)
    db.session.commit()

    return redirect(url_for("edit", id=post.id))

@app.route("/edit/<int:id>", methods=["GET","POST"])
@requires_authentication
def edit(id):
    try:
        post = db.session.query(Post).filter_by(id=id).one()
    except Exception:
        return abort(404)

    if request.method == "GET":
        return render_template("edit.html", post=post)
    else:
        if post.title != request.form.get("post_title", ""):
            post.title = request.form.get("post_title","")
            post.slug = slugify(post.title)
        post.text = request.form.get("post_content","")
        post.updated_at = datetime.datetime.now()

        if any(request.form.getlist("post_draft", type=int)):
            post.draft = True
        else:
            post.draft = False

        db.session.add(post)
        db.session.commit()
        return redirect(url_for("edit", id=id))

@app.route("/delete/<int:id>", methods=["GET","POST"])
@requires_authentication
def delete(id):
    try:
        post = db.session.query(Post).filter_by(id=id).one()
    except Exception:
        flash("Error deleting post ID %s"%id, category="error")
    else:
        db.session.delete(post)
        db.session.commit()

    return redirect(request.args.get("next","") or request.referrer or url_for('index'))

@app.route("/admin", methods=["GET", "POST"])
@requires_authentication
def admin():
    drafts = db.session.query(Post).filter_by(draft=True)\
                                          .order_by(Post.created_at.desc()).all()
    posts  = db.session.query(Post).filter_by(draft=False)\
                                          .order_by(Post.created_at.desc()).all()
    return render_template("admin.html", drafts=drafts, posts=posts)

@app.route("/admin/save/<int:id>", methods=["POST"])
@requires_authentication
def save_post(id):
    try:
        post = db.session.query(Post).filter_by(id=id).one()
    except Exception:
        return abort(404)
    if post.title != request.form.get("title", ""):
        post.title = request.form.get("title","")
        post.slug = slugify(post.title)
    post.text = request.form.get("content", "")
    post.updated_at = datetime.datetime.now()
    db.session.add(post)
    db.session.commit()
    return jsonify(success=True)

@app.route("/preview/<int:id>")
@requires_authentication
def preview(id):
    try:
        post = db.session.query(Post).filter_by(id=id).one()
    except Exception:
        return abort(404)

    return render_template("post_preview.html", post=post)

@app.route("/posts.rss")
def feed():
    posts = db.session.query(Post).filter_by(draft=False).order_by(Post.created_at.desc()).limit(10).all()

    r = make_response(render_template('index.xml', posts=posts))
    r.mimetype = "application/xml"
    return r

def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    slug = unicode(delim.join(result))
    # This could have issues if a post is marked as draft, then live, then draft, then live and there are > 1 posts
    # with the same slug. Oh well.
    _c = db.session.query(Post).filter_by(slug=slug).count()
    if _c > 0:
        return "%s%s%s"%(slug, delim, _c)
    else:
        return slug

if __name__ == "__main__":
    app.run()