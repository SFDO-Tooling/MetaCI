web: gunicorn config.wsgi:application
worker: python manage.py rqworkers default
worker_short: python manage.py rqworkers short --workers 5
