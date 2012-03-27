from simple import db
import markdown

class Post(db.Model):
    __tablename__ = "posts"
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), unique=True)
    slug  = db.Column(db.String(), unique=True)
    text  = db.Column(db.String(), default="")
    draft = db.Column(db.Boolean(), index=True, default=True)
    created_at = db.Column(db.DateTime, index=True)
    updated_at = db.Column(db.DateTime)

    def render_content(self):
        return markdown.Markdown(extensions=['fenced_code'], output_format="html5", safe_mode=True).convert(self.text)