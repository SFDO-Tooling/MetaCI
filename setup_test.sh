#!/bin/bash

python /app/manage.py populate_db
python /app/manage.py metaci_scheduled_jobs
python /app/manage.py createsuperuser


# echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('test', 'test@salesforce.com', 'password')" | python manage.py shell


