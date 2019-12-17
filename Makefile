.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

clean-test:
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -f output.xml
	rm -f report.html

test: 
	pytest

coverage: clean-test
	coverage run --source metaci -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html
