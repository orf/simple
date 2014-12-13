Simple
======

# Quickstart:

    >> mkdir blog && cd blog
    >> virtualenv env
    >> source env/bin/activate && pip install simpleblogging gunicorn
    >> simple create
    >> simple nginx_config yoursite.com --proxy-port=9009 > /etc/nginx/conf.d/simple.conf
    >> simple supervisor_config env/ 9009 >> /etc/supervisord.conf
    >> chown -R nobody:nobody ../blog
    >> supervisorctl start simple && service nginx reload