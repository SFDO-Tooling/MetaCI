web: gunicorn config.wsgi:application
worker: honcho start -f Procfile_workers
worker_short: honcho start -f Procfile_worker_short
dev_worker: honcho start -f Procfile_dev_worker
robot_worker: python manage.py metaci_rqworker robot --worker-class metaci.build.worker.RequeueingWorker --sentry-dsn=""
release: python manage.py migrate --noinput
