FROM python:3.8

ARG BUILD_ENV
ARG CHROME_VERSION
ARG CHROMEDRIVER_VERSION

RUN mkdir -p /app/.apt/usr/bin

# Set up the Chrome PPA
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Update the package list and install chrome
RUN apt-get update -y
RUN apt-get install -y google-chrome-stable
COPY ./docker/utility/wrap_chrome_binary.sh /app/docker/utility/wrap_chrome_binary.sh
RUN /app/docker/utility/wrap_chrome_binary.sh
RUN ln -fs /usr/bin/google-chrome /usr/bin/chrome

# Set up Chromedriver Environment variables
ENV CHROMEDRIVER_VERSION 79.0.3945.36
ENV CHROMEDRIVER_DIR /chromedriver
RUN mkdir $CHROMEDRIVER_DIR

# Download and install Chromedriver
RUN wget -q --continue -P $CHROMEDRIVER_DIR "http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
RUN unzip $CHROMEDRIVER_DIR/chromedriver* -d $CHROMEDRIVER_DIR

# Put Chromedriver into the PATH
ENV PATH $CHROMEDRIVER_DIR:$PATH

# declaring necessary node and yarn versions
ENV NODE_VERSION 10.16.3
# installing node
COPY ./docker/utility/install_node.sh /app/docker/utility/install_node.sh
RUN /bin/sh /app/docker/utility/install_node.sh

# declaring necessary node and yarn versions
ENV YARN_VERSION 1.19.1
# installing yarn
COPY ./docker/utility/install_yarn.sh /app/docker/utility/install_yarn.sh
RUN /bin/sh /app/docker/utility/install_yarn.sh

# installing sfdx
COPY ./docker/utility/install_sfdx.sh /app/docker/utility/install_sfdx.sh
RUN /bin/sh /app/docker/utility/install_sfdx.sh

# installing python related dependencies with pip
COPY ./requirements /app/requirements
RUN pip install --no-cache --upgrade pip
RUN if [ "${BUILD_ENV}" = "production" ] ; then pip install --no-cache -r /app/requirements/production.txt ; else pip install --no-cache -r /app/requirements/local.txt ; fi

# installing yarn dependencies
COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
WORKDIR /app
RUN yarn install
# copying rest of working directory to /app folder
COPY . /app
ENV PYTHONUNBUFFERED 1

# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# setting default environment variables which can be overridden
# in docker-compoose
ENV REDIS_URL "redis://redis:6379"
ENV DJANGO_SETTINGS_MODULE config.settings.local
ENV DATABASE_URL postgres://metaci@postgres:5432/metaci
ENV DJANGO_HASHID_SALT 'sample hashid salt'
ENV DJANGO_SECRET_KEY 'sample secret key'

# Avoid building prod assets in development
RUN if [ "${BUILD_ENV}" = "production" ] ; then yarn prod ; else mkdir -p dist/prod ; fi
RUN python /app/manage.py collectstatic --noinput
