"""Functions for renaming files based on metadata"""

# Copyright 2012-2014 Anthony Beville

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
import re
import datetime
import sys

from pathvalidate import sanitize_filepath

from . import utils
from .issuestring import IssueString


class FileRenamer:

    def __init__(self, metadata):
        self.setMetadata(metadata)
        self.setTemplate(
            "{publisher}/{series} {seriesYear}/{series} #{issue} - {title} ({year})")
        self.smart_cleanup = True
        self.issue_zero_padding = 3
        self.move = False

    def setMetadata(self, metadata):
        self.metdata = metadata

    def setIssueZeroPadding(self, count):
        self.issue_zero_padding = count

    def setSmartCleanup(self, on):
        self.smart_cleanup = on

    def setTemplate(self, template):
        self.template = template

    def replaceToken(self, text, value, token):
        # helper func
        def isToken(word):
            return (word[0] == "{" and word[-1:] == "{")

        if value is not None:
            return text.replace(token, str(value))
        else:
            if self.smart_cleanup:
                # smart cleanup means we want to remove anything appended to token if it's empty
                # (e.g "#{issue}"  or "v{volume}")
                # (TODO: This could fail if there is more than one token appended together, I guess)
                text_list = text.split()

                # special case for issuecount, remove preceding non-token word,
                # as in "...(of {issuecount})..."
                # if token == '{issuecount}':
                for idx, word in enumerate(text_list):
                    if isToken(word) and text_list[idx - 1].lower() == word[1:-1]:
                        text_list[idx - 1] = ""

                text_list = [x for x in text_list if token not in x]
                return " ".join(text_list)
            else:
                return text.replace(token, "")

    def determineName(self, filename, ext=None):
        class Default(dict):
            def __missing__(self, key):
                return "{" + key + "}"
        md = self.metdata

        month = int(md.month.strip() or 1)
        day = int(md.day.strip() or 1)
        year = int(md.year.strip() or 1)
        if day < 1:
            day = 1
        if month < 1:
            month = 1
        md.date = datetime.date(int(year), int(month), int(day))

        # padding for issue
        md.issue = IssueString(md.issue).asString(pad=self.issue_zero_padding)

        # datetemplates = re.findall('\{date:.*?\}',self.template)
        # for template in datetemplates:
        #     self.template = re.sub("(\s+%[HIpMSfzZ](})$|(\s+)%[HIpMSfzZ] )", "\\2\\3")

        template = self.template
        if self.smart_cleanup:
            template = re.sub("\s+", " ", self.template)

        pathComponents = template.split(os.sep)
        new_name = ""

        for Component in pathComponents:
            new_name = os.path.join(new_name, Component.format_map(
                Default(vars(md))).replace("/", "-"))

        if self.smart_cleanup:

            # remove empty braces,brackets, parentheses
            new_name = re.sub("[\(\[\{]\s*[-:]*\s*[\)\]\}]", "", new_name)

            # remove remove empty volume, issuenumber

            # remove remove duplicate -, _,
            new_name = re.sub("[-_]{2,}", "-", new_name)
            new_name = re.sub("(\s+-)+", " -", new_name)

            # remove dash or double dash at end of line
            new_name = re.sub("[-]{1,}\s*$", "", new_name)
            new_name = re.sub("[-#]{1,}\s+\(", "(", new_name)
            new_name = re.sub("[-#]{1,}\s+\(", "(", new_name)

            # remove duplicate spaces
            new_name = re.sub("\s+", " ", new_name)
            new_name = re.sub("\s$", "", new_name)

        if ext is None:
            ext = os.path.splitext(filename)[1]

        new_name += ext

        # some tweaks to keep various filesystems happy
        new_name = new_name.replace(": ", " - ")
        new_name = new_name.replace(":", "-")

        # remove padding
        md.issue = IssueString(md.issue).asString()
        if self.move:
            return sanitize_filepath(new_name.strip())
        else:
            return os.path.basename(sanitize_filepath(new_name.strip()))
