#!/usr/bin/python3
"""Find all duplicate comics"""

import sys
import json

from comictaggerlib.comicarchive import *
from comictaggerlib.settings import *
from comictaggerlib.issuestring import *
import comictaggerlib.utils
import subprocess
import os


def main():
#    utils.fix_output_encoding()
    settings = ComicTaggerSettings()

    style = MetaDataStyle.CIX

    if len(sys.argv) < 2:
        print("Usage:  {0} [comic_folder]".format(sys.argv[0]))
        return

    dupecmp = os.path.join(os.getcwd(), "dupecmp")
    if os.path.exists(dupecmp):
        subprocess.run(["bash", "-c", "rm -rf *"], cwd=dupecmp)
    else:
        os.mkdir(dupecmp)
    filelist = utils.get_recursive_filelist(sys.argv[1:])

    # first find all comics with metadata
    print("Reading in all comics...", file=sys.stderr)
    comic_list = []
    fmt_str = ""
    max_name_len = 2
    for filename in filelist:
        ca = ComicArchive(filename, settings.rar_exe_path, default_image_path='/home/timmy/build/source/comictagger-test/comictaggerlib/graphics/nocover.png')
        if ca.seemsToBeAComicArchive() and ca.hasMetadata(style):
            fmt_str = "{{0:{0}}}".format(max_name_len)
            print(fmt_str.format(filename) + "\r", end='', file=sys.stderr)
            sys.stderr.flush()
            comic_list.append((filename, ca.readMetadata(style)))
            max_name_len = len(filename)

    print("", file=sys.stderr)
    print("--------------------------------------------------------------------------", file=sys.stderr)
    print("Found {0} comics with {1} tags".format(len(comic_list), MetaDataStyle.name[style]), file=sys.stderr)
    print("--------------------------------------------------------------------------", file=sys.stderr)

    # sort the list by series+issue+year, to put all the dupes together
    def makeKey(x):
        return "<" + str(x[1].series) + " #" + \
            str(x[1].issue) + " - " + str(x[1].title) + " - " + str(x[1].year) + ">"
    comic_list.sort(key=makeKey, reverse=False)

    # look for duplicate blocks
    dupe_set_list = list()
    dupe_set = list()
    prev_key = ""
    for filename, md in comic_list:
        # sys.stderr.flush()

        new_key = makeKey((filename, md))

        # if the new key same as the last, add to to dupe set
        if new_key == prev_key:
            dupe_set.append(filename)

        # else we're on a new potential block
        else:
            # only add if the dupe list has 2 or more
            if len(dupe_set) > 1:
                dupe_set_list.append(dupe_set)
            dupe_set = list()
            dupe_set.append(filename)

        prev_key = new_key

    if len(dupe_set) > 1:
        dupe_set_list.append(dupe_set)


    # print(json.dumps(dupe_set_list, indent=4))
    # print(fmt_str.format("") + "\r", end=' ', file=sys.stderr)
    # print("Found {0} duplicate sets".format(len(dupe_set_list)))


    for dupe_set in dupe_set_list:
        subprocess.run(["cp"] + dupe_set + [dupecmp])
        subprocess.run(["dup-comic.sh"], cwd=dupecmp)


    #     ca = ComicArchive(dupe_set[0], settings.rar_exe_path)
    #     md = ca.readMetadata(style)
    #     print("{0} #{1} ({2})".format(md.series, md.issue, md.year))
    #     for filename in dupe_set:
    #         print("------>{0}".format(filename))

#if __name__ == '__main__':
main()
