web: gunicorn config.wsgi:application
worker: celery worker --app=config --loglevel=info --concurrency=4
