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

from __future__ import print_function

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import pathlib

import setuptools.command.build_py
import setuptools.command.install
from setuptools import Command, dist, setup

python_requires = (">=3",)


with open("requirements.txt") as f:
    required = f.read().splitlines()
# Always require PyQt5 on Windows and Mac
if platform.system() in ["Windows", "Darwin"]:
    required.append("PyQt5")


setup(
    name="comictagger",
    install_requires=required,
    description="A cross-platform GUI/CLI app for writing metadata to comic archives",
    author="ComicTagger team",
    author_email="comictagger@gmail.com",
    url="https://github.com/comictagger/comictagger",
    packages=["comictaggerlib", "comicapi"],
    package_data={"comictaggerlib": ["ui/*", "graphics/*", "*.so"],},
    entry_points=dict(console_scripts=["comictagger=comictaggerlib.main:ctmain"]),
    use_scm_version={"write_to": "comictaggerlib/ctversion.py"},
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
* Reads and writes RAR and Zip archives (external tools needed for writing RAR)
* Command line interface (CLI) on all platforms (including Windows), which supports batch operations, and which can be used in native scripts for complex operations.
* Can run without PyQt5 installed
""",
)
