web: gunicorn config.wsgi:application
worker: python manage.py rqworkers default --workers 2 --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_short: honcho start -f Procfile_worker_short
