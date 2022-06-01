import selenium
import selenium.webdriver
import sys
options = selenium.webdriver.chrome.options.Options()
options.headless = True
try:
    selenium.webdriver.Chrome(options=options)
except Exception as e:
    print(f"Unable to open chrome:\n{e}")
    sys.exit(1)
