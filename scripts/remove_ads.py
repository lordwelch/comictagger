#!/usr/bin/python
"""
Create new comic archives from old one, removing  pages marked as ads
and deleted. Walks recursively through the given folders.  Originals
are kept in a sub-folder at the level of the original
"""

# Copyright 2013 Anthony Beville

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import sys
import tempfile
import zipfile

import comictaggerlib.utils
from comictaggerlib.comicarchive import *
from comictaggerlib.settings import *

subfolder_name = "PRE_AD_REMOVAL"
unwanted_types = ["Deleted", "Advertisement"]


def main():
    # utils.fix_output_encoding()
    settings = ComicTaggerSettings()

    # this can only work with files with ComicRack tags
    style = MetaDataStyle.CIX

    if len(sys.argv) < 2:
        print("Usage: {0} [comic_folder]".format(sys.argv[0]), file=sys.stderr)
        return

    if sys.argv[1] == "-n":
        filelist = utils.get_recursive_filelist(sys.argv[2:])
    else:
        filelist = utils.get_recursive_filelist(sys.argv[1:])

    # first read in CIX metadata from all files, make a list of candidates
    modify_list = []
    for filename in filelist:
        print(filename, end="\n")

        ca = ComicArchive(
            filename,
            settings.rar_exe_path,
            default_image_path="/home/timmy/build/source/comictagger-test/comictaggerlib/graphics/nocover.png",
        )
        if (ca.isZip or ca.isRar()) and ca.hasMetadata(style):
            md = ca.readMetadata(style)
            if len(md.pages) != 0:
                pgs = list()
                mod = False
                for p in md.pages:
                    if "Type" in p and p["Type"] in unwanted_types:
                        # This one has pages to remove. Remove it!
                        print("removing " + ca.getPageName(int(p["Image"])))
                        if sys.argv[1] != "-n":
                            mod = True
                            ca.archiver.removeArchiveFile(ca.getPageName(int(p["Image"])))
                    else:
                        pgs.append(p)

                if mod:
                    for num, p in enumerate(pgs):
                        p["Image"] = str(num)
                    md.pages = pgs
                    ca.writeCIX(md)


if __name__ == "__main__":
    main()
