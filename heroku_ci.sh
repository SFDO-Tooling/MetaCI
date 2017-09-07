#!/bin/bash
# This script runs the tests on Heroku CI

#git clone -b "$HEROKU_TEST_RUN_BRANCH" --single-branch https://github.com/SalesforceFoundation/mrbelvedereci_checkout 
#cd mrbelvedereci_checkout
#git reset --hard $HEROKU_TEST_RUN_COMMIT_VERSION
coverage run --source=mrbelvedereci manage.py test
#nosetests --with-tap --tap-stream --with-coverage --cover-package=cumulusci
#coveralls
