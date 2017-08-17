release: python manage.py migrate --no-input
web: gunicorn config.wsgi:application
worker: python manage.py rqworker default --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_short: honcho start -f Procfile_worker_short
