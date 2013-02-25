""" utility for generating a configuration file for a simple blog """
from werkzeug.security import generate_password_hash
from os import urandom
from base64 import b32encode

def input_with_default(prompt, default):
    """ Small wrapper around raw_input for prompting and defaulting """
    response = raw_input("%s (Default %s) "%(prompt, default))
    if not response:
        return default
    return response

print "Generating a Simple config file. Please answer some questions:"
SETTINGS = (
    input_with_default("Posts per page", 5),
    input_with_default("Show the post content on the homepage","y").lower()[0] == "y",
    input_with_default("Show post view count on the homepage?","n").lower()[0] == "y",
    input_with_default("Admin username","admin"),
    generate_password_hash(input_with_default("Admin password","password")), 
    input_with_default("Google analytics ID",""),
    input_with_default("Database URI","sqlite:///simple.db"),
    input_with_default("Github Username", ""),
    input_with_default("Contact Email", ""),
    input_with_default("Blog title", ""),
    input_with_default("Blog tagline", ""),
    input_with_default("Blog URL (e.g. /blog)","/"),
    input_with_default("Font Name (Selected from google font library): ","Source Sans Pro").replace(" ","+"),
    input_with_default("Secret key", b32encode(urandom(32))),
    input_with_default("Disqus Shortname", "",
    )
)

with open("settings.py", "w") as fd:
    fd.write("""# -*- coding: utf-8 -*-\n
POSTS_PER_PAGE = %s
POST_CONTENT_ON_HOMEPAGE = %s
SHOW_VIEWS_ON_HOMEPAGE = %s
ADMIN_USERNAME = '%s'
ADMIN_PASSWORD = '%s'
ANALYTICS_ID = '%s'
SQLALCHEMY_DATABASE_URI = "%s"
GITHUB_USERNAME = '%s'
CONTACT_EMAIL = '%s'
BLOG_TITLE = "%s"
BLOG_TAGLINE = "%s"
BLOG_URL = '%s'
FONT_NAME = '%s',
SECRET_KEY = '%s',
DISQUS_SHORTNAME = '%s'\n""" % SETTINGS)
    fd.flush()

print "Created!"
