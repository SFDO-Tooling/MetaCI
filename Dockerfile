FROM python:3.8

ARG BUILD_ENV
RUN mkdir /app
#============================================
# Google Chrome
#============================================
# can specify versions by CHROME_VERSION;
#  e.g. google-chrome-stable=53.0.2785.101-1
#       google-chrome-beta=53.0.2785.92-1
#       google-chrome-unstable=54.0.2840.14-1
#       latest (equivalent to google-chrome-stable)
#       google-chrome-beta  (pull latest beta)
#============================================
ARG CHROME_VERSION="google-chrome-stable"
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update -qqy \
    && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
    && rm /etc/apt/sources.list.d/google-chrome.list \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#=================================
# Chrome Launch Script Wrapper
#=================================
COPY /utility/wrap_chrome_binary /opt/bin/utility/wrap_chrome_binary
RUN /opt/bin/utility/wrap_chrome_binary

# USER seluser

#============================================
# Chrome webdriver
#============================================
# can specify versions by CHROME_DRIVER_VERSION
# Latest released version will be used by default
#============================================
ARG CHROME_DRIVER_VERSION
RUN if [ -z "$CHROME_DRIVER_VERSION" ]; \
    then CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") \
    && CHROME_DRIVER_VERSION=$(wget --no-verbose -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}"); \
    fi \
    && echo "Using chromedriver version: "$CHROME_DRIVER_VERSION \
    && wget --no-verbose -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && rm -rf /opt/selenium/chromedriver \
    && unzip /tmp/chromedriver_linux64.zip -d /opt/selenium \
    && rm /tmp/chromedriver_linux64.zip \
    && mv /opt/selenium/chromedriver /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION \
    && chmod 755 /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION \
    && ln -fs /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION /usr/bin/chromedriver


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
