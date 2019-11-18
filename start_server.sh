#!/bin/bash

/usr/local/bin/python /app/manage.py migrate
if [ "${BUILD_ENV}" = "development" ] ; then
    echo "POPULATING DATABASE WITH TEST DATA"
    /usr/local/bin/python /app/manage.py populate_db;
    /usr/local/bin/python /app/manage.py metaci_scheduled_jobs;
    echo "CREATING ADMIN USER FOR TESTING PURPOSES"
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@salesforce.com', 'password')" | /usr/local/bin/python manage.py shell
fi
echo "ALL DONE!"
 
# /usr/local/bin/yarn serve
/usr/local/bin/python /app/manage.py runserver 0.0.0.0:8000 \
& /app/node_modules/.bin/webpack-dev-server --config /app/webpack.dev.js \
& /usr/local/bin/python /app/manage.py metaci_rqworker short \
& /usr/local/bin/python /app/manage.py rqscheduler --queue short