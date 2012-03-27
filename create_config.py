import os

def input_with_default(prompt, default):
    x = raw_input("%s (Default %s) "%(prompt, default))
    if not x:
        return default
    return x

with open("settings.py", "w") as fd:
    print "Generating a Simple config file. Please answer some questions:"
    fd.write('SECRET_KEY = r"%s"\n'%os.urandom(128))
    fd.write("POSTS_PER_PAGE = %s\n"%input_with_default("Posts per page", 5))
    fd.write("ADMIN_USERNAME = '%s'\n"%input_with_default("Admin username","admin"))
    fd.write("ADMIN_PASSWORD = '%s'\n"%input_with_default("Admin password","password"))
    fd.write("ANALYTICS_ID = '%s'\n"%input_with_default("Google analytics ID",""))
    fd.write('SQLALCHEMY_DATABASE_URI = "%s"'%input_with_default("Database URI","sqlite:///simple.db"))
    fd.write("GITHUB_USERNAME = '%s'"%input_with_default("Github Username", ""))
    fd.write("CONTACT_EMAIL = '%s'"%input_with_default("Contact Email", ""))
    fd.write("BLOG_TITLE = '%s'"%input_with_default("Blog title", ""))
    fd.write("BLOG_TAGLINE = '%s'"%input_with_default("Blog tagline", ""))
    fd.write("BLOG_URL = '%s'"%input_with_default("Blog URL",""))
    fd.flush()

print "Created!"
raw_input()