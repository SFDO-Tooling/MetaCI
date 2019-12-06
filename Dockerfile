FROM python:3.8

ARG BUILD_ENV
ARG CHROME_VERSION
ARG CHROME_DRIVER_VERSION
RUN mkdir /app

# declaring necessary node and yarn versions
ENV NODE_VERSION 10.16.3
# installing node
COPY ./utility/install_node.sh /app/utility/install_node.sh
RUN /bin/sh /app/utility/install_node.sh
# declaring necessary node and yarn versions
ENV YARN_VERSION 1.19.1
# installing yarn
COPY ./utility/install_yarn.sh /app/utility/install_yarn.sh
RUN /bin/sh /app/utility/install_yarn.sh
# Installing Google Chrome
COPY ./utility/install_chrome.sh /app/utility/install_chrome.sh
RUN /bin/sh /app/utility/install_chrome.sh
# Installing Chromedriver
COPY ./utility/install_chrome.sh /app/utility/install_chrome.sh
RUN /bin/sh /app/utility/install_chrome.sh
# # installing sfdx
COPY ./utility/install_sfdx.sh /app/utility/install_sfdx.sh
RUN /bin/sh /app/utility/install_sfdx.sh
# installing python related dependencies with pip
COPY ./requirements /app/requirements
RUN pip install --no-cache --upgrade pip
RUN if [ "${BUILD_ENV}" = "production" ] ; then pip install --no-cache -r /app/requirements/production.txt ; else pip install --no-cache -r /app/requirements/local.txt ; fi
COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
WORKDIR /app
RUN yarn install
# copying rest of working directory to /app folder
COPY . /app
ENV PYTHONUNBUFFERED 1
# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV REDIS_URL "redis://redis:6379"
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV DATABASE_URL postgres://metaci@postgres:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'
# Avoid building prod assets in development
RUN if [ "${BUILD_ENV}" = "production" ] ; then yarn prod ; else mkdir -p dist/prod ; fi
RUN python /app/manage.py collectstatic --noinput
# adding for Heroku
CMD ["/app/utility/start_server.sh"]
