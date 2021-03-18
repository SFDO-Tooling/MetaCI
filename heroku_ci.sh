#!/bin/bash
# This script runs the tests on Heroku CI

set -x

# Pretend this is a git repo so that coveralls can find git info
git clone -b "$HEROKU_TEST_RUN_BRANCH" --single-branch https://github.com/SFDO-Tooling/MetaCI MetaCI_checkout 
cd MetaCI_checkout
git reset --hard $HEROKU_TEST_RUN_COMMIT_VERSION
cd ..
mv MetaCI_checkout/.git ./
rm -rf MetaCI_checkout

export DJANGO_SETTINGS_MODULE=config.settings.test

# Enable coveralls parallel mode so we can report for both Python & JS
export COVERALLS_PARALLEL=true
# Coveralls doesn't recognize the Heroku CI environment automatically.
# So let's pretend we're CircleCI.
export CIRCLECI=true
export CIRCLE_BUILD_NUM=$HEROKU_TEST_RUN_ID

# Check for missing Django db migrations
DATABASE_URL=sqlite://:memory: ./manage.py makemigrations --check --dry-run || exit 1

# Run Python tests
coverage run $(which pytest) metaci --tap-stream
exit_status=$?
if [ $exit_status -eq 0 ]
then
    $(which pytest) integration-tests
    exit_status=$?
fi
coveralls

# Run JS tests
yarn test:coverage
exit_status=$exit_status || $?
cat ./coverage/lcov.info | /app/node_modules/.bin/coveralls

curl -k "https://coveralls.io/webhook?repo_token=${COVERALLS_REPO_TOKEN}" -d "payload[build_num]=${HEROKU_TEST_RUN_ID}&payload[status]=done"
if [ "$exit_status" != "0" ]; then
    exit $exit_status
fi
