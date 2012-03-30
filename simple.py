from functools import wraps
import hashlib
from flask import render_template, request, Response, Flask, flash, redirect, url_for, abort, jsonify, Response
import re
from unicodedata import normalize
from flaskext.sqlalchemy import SQLAlchemy
import datetime
from unicodedata import normalize
import markdown

app = Flask(__name__)
app.config.from_object('settings')
db = SQLAlchemy(app)

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

class Post(db.Model):
    __tablename__ = "posts"
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), unique=True)
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

def requires_authentication(f):
    @wraps(f)
    def _auth_decorator(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == app.config["ADMIN_USERNAME"]
                            and hashlib.md5(auth.password).hexdigest() == app.config["ADMIN_PASSWORD"]):
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
                                         is_more=is_more, current_page=page)

@app.route("/<int:post_id>")
def view_post(post_id):
    try:
        post = db.session.query(Post).filter_by(id=post_id, draft=False).one()
    except Exception:
        return abort(404)

    db.session.query(Post).filter_by(id=post_id).update({Post.views:Post.views+1})
    db.session.commit()

    return render_template("view.html", post=post)

@app.route("/<slug>")
def view_post_slug(slug):
    try:
        post = db.session.query(Post).filter_by(slug=slug,draft=False).one()
    except Exception:
        return abort(404)

    db.session.query(Post).filter_by(slug=slug).update({Post.views:Post.views+1})
    db.session.commit()

    pid = request.args.get("pid", "0")
    return render_template("view.html", post=post, pid=pid)

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
        title = request.form.get("post_title","")
        text  = request.form.get("post_content","")
        post.title = title
        post.slug = slugify(post.title)
        post.text  = text
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
    def generate_feed():
        yield '<?xml version="1.0" encoding="UTF-8"?>\n'
        yield '<rss version="2.0">\n'
        yield '   <channel>\n'
        yield '      <title>%s</title>\n'%app.config["BLOG_TITLE"]
        yield '      <description>%s</title>\n'%app.config["BLOG_TAGLINE"]
        yield '      <link>%s</link>\n'%app.config["BLOG_URL"]
        for post in db.session.query(Post).filter_by(draft=False).order_by(Post.created_at.desc()).all():
            yield "         <item>\n"
            yield "            <title>%s</title>\n"%post.title
            if post.text:
                yield "            <description>%s</description>\n"%post.render_content()
            else:
                yield "            <description>No content</description>\n"
            yield "            <pubDate>%s</pubDate>\n"%post.created_at.strftime('%B %d, %Y')
            yield "            <link>%s</link>\n"%("%s/%s"%(app.config["BLOG_URL"], post.slug ))
            yield "            <guid>%s</guid>\n"%("%s/%s"%(app.config["BLOG_URL"], post.slug ))
            yield "         </item>\n"
        yield "   </channel>\n"
        yield "</rss>"

    return Response(generate_feed(), mimetype="application/rss+xml")

def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


if __name__ == "__main__":
    app.run()