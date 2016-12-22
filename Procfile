web: gunicorn config.wsgi:application
worker: celery worker --app=config --loglevel=info --concurrency=4 --prefetch-multiplier=1
