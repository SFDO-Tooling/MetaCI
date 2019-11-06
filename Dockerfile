FROM python:3

# Ensure console output looks familiar
ENV PYTHONUNBUFFERED 1
# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# ENV GITHUB_WEBHOOK_SECRET "password"
# ENV CONNECTED_APP_CLIENT_ID 123
ENV REDIS_URL "redis://localhost:6379"

ENV DJANGO_SETTINGS_MODULE config.settings.local
RUN pip install --no-cache --upgrade pip


# ENV DATABASE_URL postgres://errors_db@db:5432/errors_db
# ENV POSTGRES_USER "postgres"
# ENV POSTGRES_PASSWORD ""

RUN mkdir /app
COPY . /app/
WORKDIR /app
RUN pip install --no-cache -r requirements/local.txt

ENV DATABASE_URL postgres://metaci@db:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'
ENV DJANGO_SETTINGS_MODULE config.settings.production