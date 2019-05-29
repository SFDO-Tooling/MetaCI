# Run Django migrations unless disabled
[ -z $SKIP_DJANGO_MIGRATIONS ] && python manage.py migrate --noinput
