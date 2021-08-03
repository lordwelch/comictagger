# Setup file for comictagger python source  (no wheels yet)
#
# The install process will attempt to compile the unrar lib from source.
# If it succeeds, the unrar lib binary will be installed with the python
# source.  If it fails, install will just continue.  On most Linux systems it
# should just work.  (Tested on a Mac system with homebrew, as well)
#
# An entry point script called "comictagger" will be created
#
# Currently commented out, an experiment at desktop integration.
# It seems that post installation tweaks are broken by wheel files.
# Kept here for further research

import os
import glob

from setuptools import setup

def read(fname):
    """
    Read the contents of a file.
    Parameters
    ----------
    fname : str
        Path to file.
    Returns
    -------
    str
        File contents.
    """
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


install_requires = read("requirements.txt").splitlines()

# Dynamically determine extra dependencies
extras_require = {}
extra_req_files = glob.glob("requirements-*.txt")
for extra_req_file in extra_req_files:
    name = os.path.splitext(extra_req_file)[0].replace("requirements-", "", 1)
    extras_require[name] = read(extra_req_file).splitlines()

# If there are any extras, add a catch-all case that includes everything.
# This assumes that entries in extras_require are lists (not single strings),
# and that there are no duplicated packages across the extras.
if extras_require:
    extras_require["all"] = sorted({x for v in extras_require.values() for x in v})


setup(
    name="comictagger",
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3",
    description="A cross-platform GUI/CLI app for writing metadata to comic archives",
    author="ComicTagger team",
    author_email="comictagger@gmail.com",
    url="https://github.com/comictagger/comictagger",
    packages=["comictaggerlib"],
    package_data={
        "comictaggerlib": ["ui/*", "graphics/*"],
    },
    entry_points=dict(console_scripts=["comictagger=comictaggerlib.main:ctmain"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Utilities",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Multimedia :: Graphics",
    ],
    keywords=["comictagger", "comics", "comic", "metadata", "tagging", "tagger"],
    license="Apache License 2.0",
    long_description="""
ComicTagger is a multi-platform app for writing metadata to digital comics, written in Python and PyQt.

Features:

* Runs on Mac OSX, Microsoft Windows, and Linux systems
* Communicates with an online database (Comic Vine) for acquiring metadata
* Uses image processing to automatically match a given archive with the correct issue data
* Batch processing in the GUI for tagging hundreds or more comics at a time
* Reads and writes multiple tagging schemes ( ComicBookLover and ComicRack).
* Reads and writes rar, zip and tar archives (external tools needed for writing RAR)
* Command line interface (CLI) on all platforms (including Windows), which supports batch operations, and which can be used in native scripts for complex operations.
* Can run without PyQt5 installed
""",
)
