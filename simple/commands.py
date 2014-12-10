from collections import namedtuple
import sqlite3
import random
import os
import pathlib
import shutil

from flask.ext.script import Manager, prompt_bool
import dateutil.parser

import simple
from simple import bing_images


try:
    from simple.app import app
except Exception:
    # Ok. So I don't know what to do here. I can't import simple.app anywhere because
    # that fails if there is not a simple_settings.py in the current working directory.
    # So if this fails we use a dummy app that lets us run at least deploy().
    # (we can't even run deploy() without a valid app, which we dont have until we run deploy.)
    from flask import Flask
    app = Flask("simple")

manager = Manager(app=app)

old_page = namedtuple("OldPost", "id title slug text draft views created_at updated_at")


@manager.command
def download_latest_image(output="header.jpg"):
    latest_headers = bing_images.get_latest_header_images()
    img = latest_headers["images"][0]
    bing_images.download_to(img["url"], output)
    return img


@manager.command
def create():
    """ Create a simple skeleton config file and the folder structure required to run Simple """
    print("Creating skeleton files in {0}".format(os.getcwd()))
    pathlib.Path("__init__.py").touch()

    for name in ("uploads", "cache", "logs"):
        directory = pathlib.Path(name)
        if not directory.exists():
            directory.mkdir()
    print("Downloading latest header image...")
    img = download_latest_image("header.jpg")

    with open("simple_settings.py", "w", encoding="utf-8") as fd:
        fd.write("# -*- coding: utf-8 -*-\n")
        fd.write("SITE_TITLE = 'Simple blog'\n")
        fd.write("SITE_HEADER = 'header.jpeg'\n")
        fd.write("SITE_HEADER_COPYRIGHT = {0}\n".format(repr(img["copyright"])))
        fd.write("BASIC_AUTH_USERNAME = ''\n")
        fd.write("BASIC_AUTH_PASSWORD = ''\n")
        fd.write("\n")
        fd.write("# Contact data:\n")
        fd.write("GITHUB_USERNAME = ''\n")
        fd.write("CONTACT_EMAIL = ''\n")
        fd.write("AUTHOR_NAME = ''\n")
        fd.write("AUTHOR_BIO = ''\n")
        fd.write("\n")
        fd.write("USE_X_SENDFILE = True  # Set this to True when in production, False in development\n")
        fd.write("CACHE_DIR = 'cache/'\n")
        fd.write("DATABASE_FILE = 'posts.db'\n")
        fd.write("SECRET_KEY = {0}\n".format(os.urandom(15)))

    print("Copying static files")
    static_root = str(pathlib.Path(simple.__file__).parent / "static")
    shutil.copytree(static_root, "static")


@manager.command
def nginx_config(domain_name, proxy_port="9000", use_pagespeed=False):
    """ Create a nginx config file and output it to stdout """
    try:
        from simple import app
    except Exception:
        print("Error: Cannot import simple. Have you created a config file?")
        return

    cwd = os.getcwd()
    static_root = str(pathlib.Path.cwd() / "static")
    result = app.app.jinja_env.get_template("nginx.jinja2").render(**locals())
    print(result)


@manager.command
def fake_posts(count=10):
    """ Create an empty database and fill it with fake posts """
    try:
        from faker import Faker
        fake = Faker()
    except ImportError:
        print("Error: python-faker is not installed. Cannot create fake data")
        return

    try:
        from simple.app import orm, Post, slugify
    except Exception:
        print("Error: Cannot import simple. Have you created a config file?")
        return

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


@manager.command
def import_existing(database_file):
    """ Import posts from an older Simple database """
    try:
        conn = sqlite3.connect(database_file)
    except sqlite3.Error:
        print("Cannot open file {0}! Are you sure it is a Sqlite database?".format(database_file))
        return

    try:
        from simple.app import orm, Post, slugify
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