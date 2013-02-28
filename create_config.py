""" utility for generating a configuration file for a simple blog """
from werkzeug.security import generate_password_hash
from os import urandom
from base64 import b32encode
import sys

try:
    import settings
    if not "--fresh" in sys.argv:
        sys.argv.append("--update")
        print "Updating. Use --fresh to over-write existing config"
except (ImportError, SyntaxError):
    settings = None


def input_with_default(name, prompt, default, func=lambda v: v, _input_func=raw_input):
    """ Small wrapper around raw_input for prompting and defaulting """
    if "--update" in sys.argv and settings is not None:
        # We are updating. If the name already exists in the settings object
        # then we ignore it and return the existing value
        try:
            return name, getattr(settings, name)
        except AttributeError:
            # Continue on and prompt the user
            pass

    response = _input_func("%s (Default %s) " % (prompt, default or "None"))
    if not response:
        return name, func(default)

    return name, func(response)


# Most likely a more elegant way to do this. Oh well.
def input_password(*args, **kwargs):
    # This should make input_with_default use getpass.getpass instead of raw_input, however
    # in PyCharm this causes issues. Stick with raw-input for now.
    name, response = input_with_default(*args, **kwargs)
    return name, generate_password_hash(response)


print "%s a Simple config file. Please answer some questions:" % ("Updating" if "--update" in sys.argv else "Generating")
SETTINGS = (
    input_with_default("POSTS_PER_PAGE", "Posts per page", 5),
    input_with_default("POST_CONTENT_ON_HOMEPAGE", "Show the post content on the homepage",
                       "y", lambda v: v.lower()[0] == "y"),
    input_with_default("SHOW_VIEWS_ON_HOMEPAGE", "Show post view count on the homepage?",
                       "n", lambda v: v.lower()[0] == "y"),
    input_with_default("ADMIN_USERNAME", "Admin username", "admin"),
    input_password("ADMIN_PASSWORD", "Admin password", "password"),
    input_with_default("ANALYTICS_ID", "Google analytics ID", ""),
    input_with_default("SQLALCHEMY_DATABASE_URI", "Database URI", "sqlite:///simple.db"),
    input_with_default("GITHUB_USERNAME", "Github Username", ""),
    input_with_default("CONTACT_EMAIL", "Contact Email", ""),
    input_with_default("BLOG_TITLE", "Blog title", ""),
    input_with_default("BLOG_TAGLINE", "Blog tagline", ""),
    input_with_default("BLOG_URL", "Blog URL (e.g. /blog)", "/"),
    input_with_default("FONT_NAME", "Font Name (Selected from google font library): ", "Source Sans Pro",
                       lambda v: v.replace(" ", "+")),
    input_with_default("SECRET_KEY", "Secret key", b32encode(urandom(32))),
    input_with_default("DISQUS_SHORTNAME", "Disqus Shortname", "")
)

with open("settings.py", "w") as fd:
    fd.write("# -*- coding: utf-8 -*-\n")
    for name, value in SETTINGS:
        if isinstance(value, basestring):
            value = "'%s'" % value.replace("'", "\\'")
        fd.write("%s = %s\n" % (name, value))
    fd.flush()

print "Created!"
