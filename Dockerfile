FROM python:3.8

ARG BUILD_ENV=dev
ARG CHROMEDRIVER_VERSION

RUN mkdir -p /app/.apt/usr/bin

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#using-pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set up the Chrome PPA
# Update the package list and install chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> \
     /etc/apt/sources.list.d/google.list \
  && apt-get update -y \
  && apt-get install --no-install-recommends -y \
     google-chrome-stable \
     jq \
  && rm -rf /var/lib/apt/lists/*

COPY ./docker/utility/wrap_chrome_binary.sh /app/docker/utility/wrap_chrome_binary.sh
RUN /app/docker/utility/wrap_chrome_binary.sh
RUN ln -fs /usr/bin/google-chrome /usr/bin/chrome

# Set up Chromedriver Environment variables
ENV CHROMEDRIVER_DIR /chromedriver
RUN mkdir $CHROMEDRIVER_DIR

# Download and install Chromedriver
COPY ./docker/utility/install_chromedriver.sh /app/docker/utility/install_chromedriver.sh
RUN /app/docker/utility/install_chromedriver.sh $CHROMEDRIVER_DIR $CHROMEDRIVER_VERSION

# Update PATH
ENV PATH $CHROMEDRIVER_DIR:./node_modules/.bin:$PATH:/app/sfdx/bin

# installing node
WORKDIR /app
COPY package.json ./
COPY ./docker/utility/install_node.sh ./docker/utility/install_node.sh
RUN /bin/sh /app/docker/utility/install_node.sh

# declaring necessary node and yarn versions
# installing yarn
COPY ./docker/utility/install_yarn.sh ./docker/utility/install_yarn.sh
RUN /bin/sh /app/docker/utility/install_yarn.sh

# installing sfdx
COPY ./docker/utility/install_sfdx.sh ./docker/utility/install_sfdx.sh
RUN /bin/sh /app/docker/utility/install_sfdx.sh

# installing python related dependencies with pip
COPY ./requirements ./requirements
RUN pip install --no-cache-dir --upgrade pip pip-tools
RUN pip install --no-cache-dir -r /app/requirements/prod.txt
RUN if [ "${BUILD_ENV}" = "dev" ]; then pip install --no-cache-dir -r /app/requirements/dev.txt; fi

# installing yarn dependencies
COPY yarn.lock ./
RUN yarn install
# copying rest of working directory to /app folder
COPY . /app

ENV DJANGO_HASHID_SALT='sample hashid=salt' \
  DJANGO_SETTINGS_MODULE=config.settings.$BUILD_ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  REDIS_URL="redis://redis:6379"

# Avoid building prod assets in development
RUN if [ "${BUILD_ENV}" = "production" ] ; then yarn prod ; else mkdir -p dist/prod ; fi
RUN if [ "${BUILD_ENV}" = "production" ]; then python /app/manage.py collectstatic --noinput; fi
