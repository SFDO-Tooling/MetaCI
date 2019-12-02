#!/bin/bash

# running django database migrations 
python /app/manage.py migrate
# creating test data if local settings are configured
if [ "${DJANGO_SETTINGS_MODULE}" = "config.settings.local" ] ; then
    echo "CREATING ADMIN USER FOR TESTING PURPOSES..."
    # Using key error as an indicator for whether or not to run database population and job scheduling scripts
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@salesforce.com', 'password')" | python manage.py shell
    if [ $? -eq 0 ] ; then
        # populating database with test repository, done only once
        echo "POPULATING DATABASE WITH TEST DATA..."
        python /app/manage.py populate_db;
        # running job scheduler 
        python /app/manage.py metaci_scheduled_jobs;
        npm rebuild node-sass
    else
        # Redirect stdout from echo command to stderr.
        echo "Admin user has already been created."
    fi
fi
# creating for authorization
echo $SFDX_HUB_KEY > /app/sfdx_hub.key
echo "AUTHORIZING SFDX via JWT key auth..."
# authorizing sfdx via jwt key authorization
sfdx force:auth:jwt:grant -u $SFDX_HUB_USERNAME -f /app/sfdx_hub.key -i $SFDX_CLIENT_ID --setdefaultdevhubusername
# starting server and webpack
yarn serve
echo "ALL DONE!"
