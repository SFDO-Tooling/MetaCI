import selenium
import selenium.webdriver
import sys,os
options = selenium.webdriver.chrome.options.Options()
options.headless = True
options.add_argument('--no-sandbox')

try:
    selenium.webdriver.Chrome(options=options)
except Exception as e:
    print(f"Unable to open chrome:\n{e}")
    sys.exit(1)
