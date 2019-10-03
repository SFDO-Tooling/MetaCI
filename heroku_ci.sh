#!/bin/bash
# This script runs the tests on Heroku CI

git clone -b "$HEROKU_TEST_RUN_BRANCH" --single-branch https://github.com/SFDO-Tooling/MetaCI MetaCI_checkout 
cd MetaCI_checkout
git reset --hard $HEROKU_TEST_RUN_COMMIT_VERSION
export DJANGO_SETTINGS_MODULE=config.settings.test
export COVERALLS_PARALLEL=true

yarn pytest:report-coverage
exit_status=$?

yarn test:report-coverage
exit_status = exit_status || $?

curl -k "https://coveralls.io/webhook?repo_token=${COVERALLS_REPO_TOKEN}" -d "payload[build_num]=${HEROKU_TEST_RUN_ID}&payload[status]=done"

#  coveralls
if [ "$exit_status" != "0" ]; then
    exit $exit_status
fi
