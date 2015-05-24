from collections import namedtuple
import sqlite3
import random
import os
import pathlib
import shutil

from flask.ext.script import Manager, prompt_bool
from flask import Flask
import dateutil.parser
import time

import simple
from simple import bing_images


DEFAULT_APP = Flask("simple")

try:
    from simple.app import app
except Exception:
    # Ok. So I don't know what to do here. I can't import simple.app anywhere because
    # that fails if there is not a simple_settings.py in the current working directory.
    # So if this fails we use a dummy app that lets us run at least deploy().
    # (we can't even run deploy() without a valid app, which we dont have until we run deploy.)
    app = DEFAULT_APP

manager = Manager(app=app)

old_page = namedtuple("OldPost", "id title slug text draft views created_at updated_at")


@manager.command
def download_latest_image(output="static/header.jpg"):
    latest_headers = bing_images.get_latest_header_images()
    img = latest_headers["images"][0]
    bing_images.download_to(img["url"], output)
    return img


@manager.command
def update_static():
    """ Copy new static files from Simple into this directory (after an update) """
    cwd_static = pathlib.Path.cwd() / "static"

    if not cwd_static.is_dir():
        print("Could not find a static directory to copy into")
        return

    static_root = pathlib.Path(simple.__file__).parent / "static"

    if app == DEFAULT_APP:
        # No real app, use header.jpeg
        header_file = cwd_static / "header.jpeg"
    else:
        header_file = cwd_static / app.config["SITE_HEADER"]

    header_data = None
    # Does a header image exist? (We want to preserve that)
    if header_file.exists():
        print("Found existing header file, preserving")
        with header_file.open("rb") as fd:
            header_data = fd.read()

    if cwd_static.exists():
        shutil.rmtree(str(cwd_static))

    shutil.copytree(str(static_root), "static")

    if header_data is not None:
        with header_file.open("wb") as fd:
            fd.write(header_data)


@manager.command
def create():
    """ Create a simple skeleton config file and the folder structure required to run Simple """
    print("Creating skeleton files in {0}".format(os.getcwd()))
    pathlib.Path("__init__.py").touch()

    for name in ("uploads", "cache", "logs", "static"):
        directory = pathlib.Path(name)
        if not directory.exists():
            directory.mkdir()

    print("Downloading latest header image...")
    img = download_latest_image()

    with open("simple_settings.py", "w", encoding="utf-8") as fd:
        fd.write("# -*- coding: utf-8 -*-\n")
        fd.write("SITE_TITLE = 'Simple blog'\n")
        fd.write("SITE_HEADER = 'header.jpg'\n")
        fd.write("SITE_HEADER_COPYRIGHT = {0}\n".format(repr(img["copyright"])))
        fd.write("PERSONA_EMAIL = ''  # Used to login to persona\n")
        fd.write("GOOGLE_ANALYTICS_ID = ''\n")
        fd.write("DISQUS_SHORTNAME = ''\n")
        fd.write("\n")
        fd.write("# Contact data:\n")
        fd.write("GITHUB_USERNAME = ''\n")
        fd.write("CONTACT_EMAIL = ''\n")
        fd.write("AUTHOR_NAME = ''\n")
        fd.write("AUTHOR_BIO = ''\n")
        fd.write("\n")
        fd.write("DEBUG = False\n  # Leave this!")
        fd.write("USE_X_SENDFILE = False  # Leave this as False unless you know what you are doing\n")
        fd.write("CACHE_DIR = 'cache/'\n")
        fd.write("DATABASE_FILE = 'posts.db'\n")
        fd.write("SECRET_KEY = {0}\n".format(os.urandom(1042)))

    print("Copying static files")
    update_static()
    print("Done! Go to /_posts/ to create a new post!")


@manager.command
def nginx_config(domain_name, proxy_port="9000", use_pagespeed=False):
    """ Create a nginx config file and output it to stdout """

    if app == DEFAULT_APP:
        print("Error: Cannot import simple. Have you created a config file?")
        return

    cwd = os.getcwd()
    static_root = str(pathlib.Path.cwd() / "static")
    uploads_folder = app.config["UPLOAD_FOLDER"]
    result = app.jinja_env.get_template("conf/nginx.jinja2").render(**locals())
    print(result)


@manager.command
def supervisor_config(virtualenv_path, proxy_port, workers=2):
    if app == DEFAULT_APP:
        print("Cannot import simple. Have you created a config file?")
        return

    appdir = os.getcwd()
    virtualenv_path = str(pathlib.Path(virtualenv_path).resolve())
    result = app.jinja_env.get_template("conf/supervisor.jinja2").render(**locals())
    print(result)

@manager.command
@manager.option("-c", "--count", dest="count")
def fake_posts(count=10):
    """ Create an empty database and fill it with fake posts """
    try:
        from faker import Faker
        fake = Faker()
    except ImportError:
        print("Error: module fake-factory is not installed. Cannot create fake data")
        return

    try:
        from simple.app import orm, Post
        from simple.util import slugify
    except Exception:
        print("Error: Cannot import simple. Have you created a config file?")
        return

    start_time = time.time()

    with orm.db_session():
        if orm.select(p for p in Post).count() == 0:
            for i in range(count):
                title = fake.lorem.sentence(100)[:100]
                content = fake.lorem.paragraphs(20)

                created = fake.date_time_this_month()
                posted = fake.date_time_this_month()
                modified = fake.date_time_this_month()

                p = Post(
                    title=title,
                    slug=slugify(title),
                    created=created,
                    posted=posted,
                    modified=modified,
                    is_special_page=False,
                    content=content,
                    draft=random.choice((True, False))
                )
            orm.commit()

    print("Created {0} posts in {1}".format(count, time.time()-start_time))

@manager.command
def import_existing(database_file):
    """ Import posts from an older Simple database """
    try:
        conn = sqlite3.connect(database_file)
    except sqlite3.Error:
        print("Cannot open file {0}! Are you sure it is a Sqlite database?".format(database_file))
        return

    try:
        from simple.app import orm, Post
        from simple.util import slugify
    except Exception:
        print("Error: Cannot import simple. Have you created a config file?")
        return

    if not prompt_bool("This will erase any existing posts inside 'posts.db'. Are you sure?"):
        return

    with orm.db_session():
        for post in orm.select(p for p in Post): post.delete()
        orm.flush()

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts;")
        for data in cursor.fetchall():
            page = old_page(*data)
            post = Post(id=page.id,
                        title=page.title,
                        slug=page.slug,
                        created=dateutil.parser.parse(page.created_at),
                        posted=dateutil.parser.parse(page.created_at),
                        modified=dateutil.parser.parse(page.updated_at),
                        content=page.text or " ",
                        is_special_page=False,
                        draft=page.draft == 1)
            pass

        orm.commit()


def main():
    manager.run()


if __name__ == "__main__":
    manager.run()