""" utility for generating a configuration file for a simple blog """
from werkzeug.security import generate_password_hash
from os import urandom
from base64 import b32encode
import sys
import getpass

if "--help" in sys.argv:
    print "create_config.py:"
    print "Options:"
    print "  * --fresh"
    print "    Over-write existing config if it exists"
    print "  * --update"
    print "    Update existing config (Default if the config exists)"
    print "  * --changepass"
    print "    Change the admin password"
    sys.exit(1)

try:
    import settings
    if not "--fresh" in sys.argv and not "--changepass" in sys.argv:
        sys.argv.append("--update")
        print "Updating. Use --fresh to over-write existing config"
except (ImportError, SyntaxError):
    settings = None


def input_with_default(*args, **kwargs):
    _type = kwargs.pop("_type", None)

    name, res = _input_with_default(*args, **kwargs)

    if _type is None:
        return name, res
    else:
        try:
            return name, _type(res)
        except ValueError:
            print "Error: Value %s is not the correct type. Please re-enter" % res
            return input_with_default(*args, _type=_type, **kwargs)


def _input_with_default(name, prompt, default, func=lambda v: v, _input_func=raw_input):
    """ Small wrapper around raw_input for prompting and defaulting """
    if ("--update" in sys.argv or ("--changepass" in sys.argv and name != "ADMIN_PASSWORD")) and settings is not None:
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
    name, response = input_with_default(*args, _input_func=getpass.getpass, **kwargs)
    return name, generate_password_hash(response)


print "%s a Simple config file. Please answer some questions:" % ("Updating" if "--update" in sys.argv else "Generating")
SETTINGS = (
    input_with_default("POSTS_PER_PAGE", "Posts per page", 5, _type=int),
    input_with_default("POST_CONTENT_ON_HOMEPAGE", "Show the post content on the homepage",
                       "y", lambda v: v.lower()[0] == "y"),
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
    input_with_default("DISQUS_SHORTNAME", "Disqus Shortname", ""),
    input_with_default("USE_ADDTOANY", "Enable AddToAny integration", "y", lambda v: v.lower()[0] == "y"),
    input_with_default("USE_SUBTOME", "Enable SubToMe integration", "n", lambda v: v.lower()[0] == "y"),
)

with open("settings.py", "w") as fd:
    fd.write("# -*- coding: utf-8 -*-\n")
    for name, value in SETTINGS:
        if isinstance(value, basestring):
            value = "'%s'" % value.replace("'", "\\'")
        fd.write("%s = %s\n" % (name, value))
    fd.flush()

print "Created!"
