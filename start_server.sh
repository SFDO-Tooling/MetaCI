#!/bin/sh
export PROJECT=$(pwd)
export PATH=$PROJECT/node/bin:$PROJECT/node_modules/.bin:$PATH
python /app/manage.py migrate
if [ "${BUILD_ENV}" = "test" ] ; then
    python /app/manage.py populate_db
    python /app/manage.py metaci_scheduled_jobs
    # python /app/manage.py createsuperuser
fi
yarn serve

 
