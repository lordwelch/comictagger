PIP ?= pip3
PYTHON ?= python3
VERSION_STR := $(shell $(PYTHON) setup.py --version)

SITE_PACKAGES := $(shell $(PYTHON) -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
PACKAGE_PATH = $(SITE_PACKAGES)/comictagger.egg-link

VENV := $(shell echo $${VIRTUAL_ENV-venv})
PY3 := $(shell command -v $(PYTHON) 2> /dev/null)
PYTHON_VENV := $(VENV)/bin/python
INSTALL_STAMP := $(VENV)/.install.stamp


ifeq ($(OS),Windows_NT)
	OS_VERSION=win-$(PROCESSOR_ARCHITECTURE)
	APP_NAME=comictagger.exe
	FINAL_NAME=ComicTagger-$(VERSION_STR)-$(OS_VERSION).exe
else ifeq ($(shell uname -s),Darwin)
	OS_VERSION=osx-$(shell defaults read loginwindow SystemVersionStampAsString)-$(shell uname -m)
	APP_NAME=ComicTagger.app
	FINAL_NAME=ComicTagger-$(VERSION_STR)-$(OS_VERSION).app
else
	APP_NAME=comictagger
	FINAL_NAME=ComicTagger-$(VERSION_STR)
endif

.PHONY: all clean pydist upload dist CI check run

all: clean dist

$(PYTHON_VENV):
	@if [ -z $(PY3) ]; then echo "Python 3 could not be found."; exit 2; fi
	$(PY3) -m venv $(VENV)

clean:
	find . -maxdepth 4 -type d -name "__pycache__"
	rm -rf $(PACKAGE_PATH) $(INSTALL_STAMP) build dist MANIFEST comictaggerlib/ctversion.py
	$(MAKE) -C mac clean

CI: ins
	black .
	isort .
	flake8 . || true
	pytest || true

check: install
	$(VENV)/bin/black --check .
	$(VENV)/bin/isort --check .
	$(VENV)/bin/flake8 .
	$(VENV)/bin/pytest

pydist:
	$(PY3) -m build

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON_VENV) requirements.txt requirements_dev.txt
	$(PYTHON_VENV) -m pip install -r requirements_dev.txt
	$(PYTHON_VENV) -m pip install -e .
	touch $(INSTALL_STAMP)

ins: $(PACKAGE_PATH)
$(PACKAGE_PATH):
	$(PIP) install -e .

dist: ins
	pyinstaller -y comictagger.spec
	cd dist && zip -m -r $(FINAL_NAME).zip $(APP_NAME)
