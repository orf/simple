Simple
======

<strong>No longer maintained</strong> - I switched my blog to Gatsby, see https://tomforb.es/goodby-simple-hello-gatsby/ .

Simple is as a Python-powered markdown blog. You can see an example running [on my blog](http://tomforb.es/). The editor is an expanding textarea and you can upload images by dragging and dropping them onto the page, and ctrl+s saves the post.

You can also add a header image to any post by selecting the image icon in the top right. This lets you browse through the latest Bing daily images, and in the future you will be able to upload your own.

## Quickstart:
It's supposed to be easy to set up Simple. If you don't think it is then open a ticket and let me know. Simple is designed to be served via Gunicorn, behind nginx. You can optionally use supervisord to manage the gunicorn processes. 

You need Python 3.4, and simply follow the commands below (nginx on Ubuntu uses /sites-available/ instead of /conf.d/):

    >> mkdir blog && cd blog
    >> python3.4 -m venv env
    >> source env/bin/activate && pip install simpleblogging gunicorn
    >> simple create
    >> nano simple_config.py
    >> simple nginx_config yoursite.com --proxy_port=9009 > /etc/nginx/conf.d/simple.conf
    >> simple supervisor_config env/ 9009 >> /etc/supervisord.conf
    >> chown -R nobody:nobody ../blog
    >> supervisorctl start simple && service nginx reload
