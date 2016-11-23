web: gunicorn config.wsgi:application
worker: celery worker --app=mrbelvedereci.taskapp --loglevel=info
