#!/usr/bin/env bash 
set -e

if [ -n "$CTC_URL" ] ; then
     # Run migration surrounded by CTC start/stop
     python .heroku/check_change_traffic_control.py
else
     # Simply run the migration
     python manage.py migrate --noinput
     python .heroku/check_change_traffic_control.py
fi

echo "Done."
