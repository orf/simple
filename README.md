Simple
================
A clone of [Obtvse](http://github.com/NateW/obtvse).

About
============
The point of Simple is to be simple. The blog is 1 file (excluding resources) with a few simple pure-python dependancies (Flask, Sqlalchemy, Markdown), it doesn't require a database server, has a small footprint and is very fast (Can easily handle 300+ requests per second).

Features
============
* Markdown goodness, no clutter or fuss when writing your posts
* Lightweight and simple
* Supports Disqus comments, Google Analytics and custom fonts (from google's font library)
* Drag and drop uploads
* Includes several Markdown extensions:
    * [CodeHilight](http://pythonhosted.org/Markdown/extensions/code_hilite.html)
    * [Fenced Code Blocks](http://pythonhosted.org/Markdown/extensions/fenced_code_blocks.html)
    * [Table of contents](http://pythonhosted.org/Markdown/extensions/toc.html)

Installation
============
Its quite simple. Go download Python 2.7+, clone this repository and then run 'pip install -r requirements.txt'.
Then create a settings file by running create_config.py and then run simple.py. If you want to add a favicon to your blog then drop one (make sure its called 'favicon.ico') in the static folder and restart simple.

### Updating
Updates to simple may add, remove or alter settings. Simple ships with a script called create_config.py which can update settings files with changes.
To do this run "create_config.py" again and you will only be prompted for settings that are not present in the existing settings.py file.

Deployment
============
Deploying Simple is easy. Simply clone this repo (or your own) and install [Gunicorn](http://gunicorn.org/).
Then cd to the directory containing simple.py and run the following command:
``gunicorn -w 4 simple:app``
This will start 4 gunicorn workers serving Simple. You can then use nginx or apache to forward requests to Gunicorn.

Example
============
You can see my blog running this software [here](http://tomforb.es/simple).

Screenshots
===========
![Admin](http://i.imgur.com/M4i0ahm.png)

![Draft](http://i.imgur.com/KkGtlTx.png)

![Live](http://i.imgur.com/tsiSsED.png)


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/orf/simple/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

