
# ComicTagger

ComicTagger is a **multi-platform** app for **writing metadata to digital comics**, written in Python and PyQt.


## Features

* Runs on macOS, Microsoft Windows, and Linux systems


For details, screen-shots, release notes, and more, visit [the Wiki](https://github.com/comictagger/comictagger/wiki)


## Installation

### Binaries

Windows and macOS binaries are provided in the [Releases Page](https://github.com/comictagger/comictagger/releases). 

Just unzip the archive in any folder and run, no additional installation steps are required.

### PIP installation

A pip package is provided, you can install it with:

```
 $ pip3 install comictagger[GUI]
```

### From source

 1. Ensure you have a recent version of python3 installed
 2. Clone this repository `git clone https://github.com/comictagger/comictagger.git`
 3. `pip3 install -r requirements_dev.txt`
 4. Optionally install the GUI `pip3 install -r requirements-GUI.txt`
 5. Optionally install CBR support `pip3 install -r requirements-CBR.txt`
 6. `python3 comictagger.py`
