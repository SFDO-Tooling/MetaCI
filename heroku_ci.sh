#!/bin/bash
# This script runs the tests on Heroku CI

export DJANGO_SETTINGS_MODULE=config.settings.test

# Enable coveralls parallel mode so we can report for both Python & JS
export COVERALLS_PARALLEL=true
# Coveralls doesn't recognize the Heroku CI environment automatically.
# So let's pretend we're CircleCI.
export CIRCLECI=true
export CIRCLE_BUILD_NUM=$HEROKU_TEST_RUN_ID
export GIT_BRANCH=$HEROKU_TEST_RUN_BRANCH
export GIT_ID=$HEROKU_TEST_RUN_COMMIT_VERSION

# Run Python tests
coverage run $(which pytest) metaci --tap-stream
exit_status=$?
coveralls

# Run JS tests
yarn test:coverage
exit_status=$exit_status || $?
cat ./coverage/lcov.info | /app/node_modules/.bin/coveralls

curl -k "https://coveralls.io/webhook?repo_token=${COVERALLS_REPO_TOKEN}" -d "payload[build_num]=${HEROKU_TEST_RUN_ID}&payload[status]=done"
if [ "$exit_status" != "0" ]; then
    exit $exit_status
fi
