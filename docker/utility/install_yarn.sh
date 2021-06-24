#!/bin/bash

# This file installs the given Yarn version to the docker image

# Check whether jq is availible, if so, read the engines.node value from package.json
if command -v jq &> /dev/null
then
    YARN_VERSION=${YARN_VERSION:-$(jq --raw-output '.engines.yarn' package.json)}
fi

set -ex
key=6A010C5166006599AA17F08146C2130DFD2497F5
gpg --batch --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys "$key" || \
gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$key" || \
gpg --batch --keyserver hkp://pgp.mit.edu:80 --recv-keys "$key"  \
  && curl -fsSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz" \
  && curl -fsSLO --compressed "https://yarnpkg.com/downloads/$YARN_VERSION/yarn-v$YARN_VERSION.tar.gz.asc" \
  && gpg --batch --verify yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz \
  && mkdir -p /opt \
  && tar -xzf yarn-v$YARN_VERSION.tar.gz -C /opt/ \
  && ln -s /opt/yarn-v$YARN_VERSION/bin/yarn /usr/local/bin/yarn \
  && ln -s /opt/yarn-v$YARN_VERSION/bin/yarnpkg /usr/local/bin/yarnpkg \
  && rm yarn-v$YARN_VERSION.tar.gz.asc yarn-v$YARN_VERSION.tar.gz
