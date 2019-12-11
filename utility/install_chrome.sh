#!/bin/bash 

# This file installs the given CHROME_VERSION to the docker container downloading 
# a stable version to the dockerfile image
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update -qqy
apt-get -qqy install ${CHROME_VERSION:-google-chrome-stable}
rm /etc/apt/sources.list.d/google-chrome.list
rm -rf /var/lib/apt/lists/* /var/cache/apt/*
