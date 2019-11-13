FROM python:3.8

ARG BUILD_ENV=development


RUN mkdir /app

COPY ./requirements /requirements
COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
COPY . /app/


RUN chmod +x ./app/get_node.sh
RUN /bin/sh /app/get_node.sh

RUN chmod +x ./app/get_yarn.sh
RUN /bin/sh /app/get_yarn.sh

WORKDIR /app

RUN yarn install
RUN pip install --no-cache --upgrade pip
RUN pip install --no-cache -r /requirements/local.txt

# Avoid building prod assets in development
RUN if [ "${BUILD_ENV}" = "production" ] ; then yarn serve ; else mkdir -p dist/prod ; fi
RUN python /app/manage.py collectstatic --noinput

ENV PYTHONUNBUFFERED 1
# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV REDIS_URL "redis://redis:6379"
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV DATABASE_URL postgres://metaci@db:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'