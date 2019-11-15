#!/bin/sh
export PROJECT=$(pwd)
export PATH=$PROJECT/node/bin:$PROJECT/node_modules/.bin:$PATH
python /app/manage.py migrate

if [ "${BUILD_ENV}" = "development" ] ; then
    python /app/manage.py populate_db;
    python /app/manage.py metaci_scheduled_jobs;
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@salesforce.com', 'password')" | python manage.py shell
fi
yarn serve

 
