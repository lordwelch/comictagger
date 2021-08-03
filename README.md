A fork from https://github.com/comictagger/comictagger

Changes:
 - switched to rarfile, makes dependencies simpler and I had issues using unrar-cffi with python<6.7
 - Move to Python requests module, requests is much simpler and fixes all ssl errors.
 - Moved to using Python format strings and use pathvalidate to handle filenames, supports directory structures
 - Issue string parsing now strips off (# of #) (e.g. 1 of 45)
 - Add publisher and imprint handling, currently hardcoded
 
Notes:
- I did some testing with the pyinstaller build, and it worked on both platforms.  I did encounter two problems:
  - Mac build showed the wrong widget set. I found a solution here that seemed to work: https://stackoverflow.com/questions/48626999/packaging-with-pyinstaller-pyqt5-setstyle-ignored
  - Windows build had problems grabbing images from ComicVine using SSL.  It think that some libraries are missing from the monolithic exe, but I couldn't figure out how to fix the problem. 
- In setup.py you can also find the remains of an attempt to do some desktop integration from a pip install.  It does work, but can cause problems with wheel installs, and I don't know if it's worth the bother.  I kept the commented-out code in place, just in case.

With Python 3, it's much easier to get the app working from scratch on a new distro, as all of the dependencies are available as wheels, including PyQt5, so just a simple "pip install comictagger.zip" is all that's needed.
