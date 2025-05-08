import selenium
import selenium.webdriver
import sys,os
options = selenium.webdriver.chrome.options.Options()
options.add_argument('--no-sandbox')
os.mkdir('/tmp/test-data')
options.add_argument('--user-data-dir=/tmp/test-data')

try:
    selenium.webdriver.Chrome(options=options)
except Exception as e:
    print(f"Unable to open chrome:\n{e}")
    sys.exit(1)
