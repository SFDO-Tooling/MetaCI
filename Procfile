web: gunicorn config.wsgi:application
worker: python manage.py rqworkers default --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_short: python manage.py rqworkers short --workers 5 --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_scheduler: python manage.py rqscheduler
