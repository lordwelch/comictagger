VERSION_STR := $(shell python -c 'import comictaggerlib._version; print( comictaggerlib._version.version)')

ifeq ($(OS),Windows_NT)
	APP_NAME=comictagger.exe
	FINAL_NAME=ComicTagger-$(VERSION_STR).exe
	ICON_PATH="windows/app.ico"
else ifeq ($(shell uname -s),Darwin)
	APP_NAME=ComicTagger.app
	FINAL_NAME=ComicTagger-$(VERSION_STR).app
	ICON_PATH="mac/app.icns"
else
	APP_NAME=comictagger
	FINAL_NAME=ComicTagger-$(VERSION_STR)
	ICON_PATH="windows/app.ico"
endif

.PHONY: all clean pydist upload dist
	
all: clean dist

clean:
	rm -rf *~ *.pyc *.pyo
	rm -rf scripts/*.pyc
	cd comictaggerlib; rm -f *~ *.pyc *.pyo
	rm -rf dist MANIFEST
	rm -rf *.deb
	rm -rf logdict*.log
	$(MAKE) -C mac clean   
	rm -rf build
	rm -rf comictaggerlib/ui/__pycache__

pydist:
	make clean
	mkdir -p piprelease
	rm -f comictagger-$(VERSION_STR).zip
	python setup.py sdist --formats=zip  #,gztar
	mv dist/comictagger-$(VERSION_STR).zip piprelease
	rm -rf comictagger.egg-info dist
		
upload:
	python setup.py register
	python setup.py sdist --formats=zip upload

dist:
	pyinstaller.exe --name="comictagger" --windowed --add-data 'comictaggerlib/ui/*.ui;ui' --add-data 'comictaggerlib/graphics;graphics' -i windows/app.ico --version-file file_version_info.py comictagger.py
	mv dist/$(APP_NAME) dist/$(FINAL_NAME)
