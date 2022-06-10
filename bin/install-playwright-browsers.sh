#!/bin/bash
GOOGLE_CHROME=/app/.apt/usr/bin/google-chrome 
PLAYWRIGHT_CHROME_FOLDER=/app/.heroku/python/lib/python3.9/site-packages/Browser/wrapper/node_modules/playwright-core/.local-browsers/chromium-1005/chrome-linux
# Clean old node side dependencies and browser binaries
rfbrowser clean-node
# Install the node dependencies but skipping browser dependencies which are 700MB+
rfbrowser init --skip-browsers
# Creating playwright chrome executable folder location
mkdir -p $PLAYWRIGHT_CHROME_FOLDER
# Create symbolic link from installed google-chrome 
# executable to playwright's expected executable 
# chrome path to resolve binary 
ln -s $GOOGLE_CHROME $PLAYWRIGHT_CHROME_FOLDER/chrome
