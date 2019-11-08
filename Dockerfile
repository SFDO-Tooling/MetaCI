FROM python:3
# RUN apt-get update
# RUN apt-get -y install npm
# RUN apt-get remove cmdtest
# RUN apt-get remove yarn
# RUN npm install -gy yarn
# RUN npm uninstall node
# RUN npm install node@10.16.3
# Ensure console output looks familiar
ENV PYTHONUNBUFFERED 1
# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV REDIS_URL "redis://localhost:6379"
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV DATABASE_URL postgres://metaci@db:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'
ENV DJANGO_SETTINGS_MODULE config.settings.production
RUN mkdir /app
COPY . /app/
COPY ./requirements /requirements
# COPY ./package.json /app/package.json
# COPY ./yarn.lock /app/yarn.lock
WORKDIR /app
# RUN yarn install
RUN pip install --no-cache --upgrade pip
RUN pip install --no-cache -r /requirements/local.txt