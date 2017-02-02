web: gunicorn config.wsgi:application
worker: python manage.py rqworker default --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_short: python manage.py rqworker short --worker-class mrbelvedereci.build.worker.RequeueingWorker
worker_scheduler: python manage.py rqscheduler
