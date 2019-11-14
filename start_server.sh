#!/bin/sh

while !</dev/tcp/postgres/5432; do sleep 1; done;
sleep 1;
python /app/manage.py migrate
if [ "${BUILD_ENV}" = "test" ] ; then
    /bin/sh /app/setup_test.sh ;
    python /app/manage.py populate_db
    python /app/manage.py metaci_scheduled_jobs
    # python /app/manage.py createsuperuser
fi
yarn serve

 
