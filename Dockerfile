FROM python:3.8

ARG BUILD_ENV=development
RUN mkdir /app
# declaring necessary node and yarn versions
ENV NODE_VERSION 10.16.3
ENV YARN_VERSION 1.19.1
ENV NODEJS_VERSION 13.0.0

COPY ./get_node.sh /app/get_node.sh
COPY ./get_nodejs.sh /app/get_nodejs.sh
COPY ./get_yarn.sh /app/get_yarn.sh
# installing node
RUN chmod +x ./app/get_node.sh
RUN /bin/sh /app/get_node.sh
# # installing nodejs
# RUN chmod +x ./app/get_nodejs.sh
# RUN /bin/sh /app/get_nodejs.sh
# installing yarn
RUN chmod +x ./app/get_yarn.sh
RUN /bin/sh /app/get_yarn.sh
COPY ./requirements /requirements
RUN pip install --no-cache --upgrade pip
RUN pip install --no-cache -r /requirements/local.txt

COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
WORKDIR /app
RUN yarn install
# RUN apt-get install -y nodejs

COPY . /app
RUN chmod +x /app/start_server.sh
ENV PYTHONUNBUFFERED 1
# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV REDIS_URL "redis://redis:6379"
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV DATABASE_URL postgres://metaci@postgres:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'

# Avoid building prod assets in development
RUN if [ "${BUILD_ENV}" = "production" ] ; then yarn serve ; else mkdir -p dist/prod ; fi
RUN python /app/manage.py collectstatic --noinput