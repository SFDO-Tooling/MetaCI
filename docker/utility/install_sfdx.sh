#!/bin/bash

# This file downloads sfdx for the Dockerfile container.
mkdir sfdx
wget -qO- https://developer.salesforce.com/media/salesforce-cli/sfdx/channels/stable/sfdx-linux-x64.tar.xz | tar xJ -C sfdx --strip-components 1
