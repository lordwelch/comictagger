"""A class for internal metadata storage

The goal of this class is to handle ALL the data that might come from various
tagging schemes and databases, such as ComicVine or GCD.  This makes conversion
possible, however lossy it might be

"""

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

from . import utils


class PageType:

    """
    These page info classes are exactly the same as the CIX scheme, since
    it's unique
    """

    FrontCover = "FrontCover"
    InnerCover = "InnerCover"
    Roundup = "Roundup"
    Story = "Story"
    Advertisement = "Advertisement"
    Editorial = "Editorial"
    Letters = "Letters"
    Preview = "Preview"
    BackCover = "BackCover"
    Other = "Other"
    Deleted = "Deleted"


"""
class PageInfo:
	Image = 0
	Type = PageType.Story
	DoublePage = False
	ImageSize = 0
	Key = ""
	ImageWidth = 0
	ImageHeight = 0
"""


class GenericMetadata:

    def __init__(self):

        self.isEmpty = True
        self.tagOrigin = ""

        self.series = ""
        self.issue = ""
        self.title = ""
        self.publisher = ""
        self.seriesYear = ""
        self.month = ""
        self.year = ""
        self.day = ""
        self.issueCount = ""
        self.volume = ""
        self.genre = ""
        self.language = ""  # 2 letter iso code
        self.comments = ""  # use same way as Summary in CIX

        self.volumeCount = ""
        self.criticalRating = ""
        self.country = ""

        self.alternateSeries = ""
        self.alternateNumber = ""
        self.alternateCount = ""
        self.imprint = ""
        self.notes = ""
        self.webLink = ""
        self.format = ""
        self.manga = ""
        self.blackAndWhite = ""
        self.pageCount = ""
        self.maturityRating = ""

        self.storyArc = ""
        self.seriesGroup = ""
        self.scanInfo = ""

        self.characters = ""
        self.teams = ""
        self.locations = ""

        self.credits = list()
        self.tags = list()
        self.pages = list()

        # Some CoMet-only items
        self.price = ""
        self.isVersionOf = ""
        self.rights = ""
        self.identifier = ""
        self.lastMark = ""
        self.coverImage = ""

    def overlay(self, new_md):
        """Overlay a metadata object on this one

        That is, when the new object has non-None values, over-write them
        to this one.
        """

        def assign(cur, new):
            if new is not None and new.strip() is not "":
                if isinstance(new, str):
                    setattr(self, cur, new.strip())
                else:
                    setattr(self, cur, new)

        if not new_md.isEmpty:
            self.isEmpty = False

        assign('series', new_md.series)
        assign("issue", new_md.issue)
        assign("issueCount", new_md.issueCount)
        assign("title", new_md.title)
        assign("publisher", new_md.publisher)
        assign("day", new_md.day)
        assign("month", new_md.month)
        assign("seriesYear", new_md.seriesYear)
        assign("year", new_md.year)
        assign("volume", new_md.volume)
        assign("volumeCount", new_md.volumeCount)
        assign("genre", new_md.genre)
        assign("language", new_md.language)
        assign("country", new_md.country)
        assign("criticalRating", new_md.criticalRating)
        assign("alternateSeries", new_md.alternateSeries)
        assign("alternateNumber", new_md.alternateNumber)
        assign("alternateCount", new_md.alternateCount)
        assign("imprint", new_md.imprint)
        assign("webLink", new_md.webLink)
        assign("format", new_md.format)
        assign("manga", new_md.manga)
        assign("blackAndWhite", new_md.blackAndWhite)
        assign("maturityRating", new_md.maturityRating)
        assign("storyArc", new_md.storyArc)
        assign("seriesGroup", new_md.seriesGroup)
        assign("scanInfo", new_md.scanInfo)
        assign("characters", new_md.characters)
        assign("teams", new_md.teams)
        assign("locations", new_md.locations)
        assign("comments", new_md.comments)
        assign("notes", new_md.notes)

        assign("price", new_md.price)
        assign("isVersionOf", new_md.isVersionOf)
        assign("rights", new_md.rights)
        assign("identifier", new_md.identifier)
        assign("lastMark", new_md.lastMark)

        self.overlayCredits(new_md.credits)
        # TODO

        # not sure if the tags and pages should broken down, or treated
        # as whole lists....

        # For now, go the easy route, where any overlay
        # value wipes out the whole list
        if len(new_md.tags) > 0:
            assign("tags", new_md.tags)

        if len(new_md.pages) > 0:
            assign("pages", new_md.pages)

    def overlayCredits(self, new_credits):
        for c in new_credits:
            if 'primary' in c and c['primary']:
                primary = True
            else:
                primary = False

            # Remove credit role if person is blank
            if c['person'] == "":
                for r in reversed(self.credits):
                    if r['role'].lower() == c['role'].lower():
                        self.credits.remove(r)
            # otherwise, add it!
            else:
                self.addCredit(c['person'], c['role'], primary)

    def setDefaultPageList(self, count):
        # generate a default page list, with the first page marked as the cover
        for i in range(count):
            page_dict = dict()
            page_dict['Image'] = str(i)
            if i == 0:
                page_dict['Type'] = PageType.FrontCover
            self.pages.append(page_dict)

    def getArchivePageIndex(self, pagenum):
        # convert the displayed page number to the page index of the file in
        # the archive
        if pagenum < len(self.pages):
            return int(self.pages[pagenum]['Image'])
        else:
            return 0

    def getCoverPageIndexList(self):
        # return a list of archive page indices of cover pages
        coverlist = []
        for p in self.pages:
            if 'Type' in p and p['Type'] == PageType.FrontCover:
                coverlist.append(int(p['Image']))

        if len(coverlist) == 0:
            coverlist.append(0)

        return coverlist

    def addCredit(self, person, role, primary=False):

        credit = dict()
        credit['person'] = person
        credit['role'] = role
        if primary:
            credit['primary'] = primary

        # look to see if it's not already there...
        found = False
        for c in self.credits:
            if (c['person'].lower() == person.lower() and
                    c['role'].lower() == role.lower()):
                # no need to add it. just adjust the "primary" flag as needed
                c['primary'] = primary
                found = True
                break

        if not found:
            self.credits.append(credit)

    def __str__(self):
        vals = []
        if self.isEmpty:
            return "No metadata"

        def add_string(tag, val):
            if val is not None and val is not "":
                vals.append((tag, val))

        def add_attr_string(tag):
            val = getattr(self, tag)
            add_string(tag, getattr(self, tag))

        add_attr_string("series")
        add_attr_string("issue")
        add_attr_string("issueCount")
        add_attr_string("title")
        add_attr_string("publisher")
        add_attr_string("year")
        add_attr_string("month")
        add_attr_string("day")
        add_attr_string("volume")
        add_attr_string("volumeCount")
        add_attr_string("genre")
        add_attr_string("language")
        add_attr_string("country")
        add_attr_string("criticalRating")
        add_attr_string("alternateSeries")
        add_attr_string("alternateNumber")
        add_attr_string("alternateCount")
        add_attr_string("imprint")
        add_attr_string("webLink")
        add_attr_string("format")
        add_attr_string("manga")

        add_attr_string("price")
        add_attr_string("isVersionOf")
        add_attr_string("rights")
        add_attr_string("identifier")
        add_attr_string("lastMark")

        if self.blackAndWhite:
            add_attr_string("blackAndWhite")
        add_attr_string("maturityRating")
        add_attr_string("storyArc")
        add_attr_string("seriesGroup")
        add_attr_string("scanInfo")
        add_attr_string("characters")
        add_attr_string("teams")
        add_attr_string("locations")
        add_attr_string("comments")
        add_attr_string("notes")

        add_string("tags", utils.listToString(self.tags))

        for c in self.credits:
            primary = ""
            if 'primary' in c and c['primary']:
                primary = " [P]"
            add_string("credit", c['role'] + ": " + c['person'] + primary)

        # find the longest field name
        flen = 0
        for i in vals:
            flen = max(flen, len(i[0]))
        flen += 1

        # format the data nicely
        outstr = ""
        fmt_str = "{0: <" + str(flen) + "} {1}\n"
        for i in vals:
            outstr += fmt_str.format(i[0] + ":", i[1])

        return outstr

    def fixPublisher(self):
        Marvel = ['Aircel Comics', 'alibu Comics‎', 'Atlas Comics', 'Atlas', 'CrossGen comics‎', 'CrossGen', 'Curtis Magazines', 'Disney Books Group', 'Disney Kingdoms', 'Epic Comics', 'Eternity Comics', 'Humorama', 'Icon Comics', 'Infinite Comics', 'Malibu Comics', 'Marvel 2099', 'Marvel Absurd', 'Marvel Adventures', 'Marvel Age', 'Marvel Books', 'Marvel Comics 2', 'Marvel Comics', 'Marvel Edge', 'Marvel Frontier', 'Marvel Illustrated',
                  'Marvel Knights', 'Marvel Magazine Group', 'Marvel Mangaverse', 'Marvel Monsters Group', 'Marvel Music', 'Marvel Next', 'Marvel Noir', 'Marvel Press', 'Marvel UK', 'Marvel Unlimited', 'Max', 'MAX', 'MC2', 'New Universe', 'Non-Pareil Publishing Corp.', 'Paramount Comics', 'Power Comics', 'Razorline', 'Star Comics', 'Timely Comics', 'Timely', 'Tsunami', 'Ultimate Comics', 'Ultimate Marvel', 'Vital Publications, Inc.', ]
        DC_Comics = ['All Star', 'Amalgam Comics', 'America\'s Best Comics', 'Cliffhanger', 'CMX Manga', 'DC Black Label', 'DC Focus', 'DC Ink', 'DC Zoom', 'DC', 'Earth-M', 'Elseworlds', 'First Wave', 'Helix', 'Homage Comics', 'Impact Comics',
                     'Johnny DC', 'Mad', 'Minx', 'Paradox Press', 'Piranha Press', 'Sandman Universe', 'Tangent Comics', 'Vertigo', 'WildStorm Productions', 'WildStorm Signature', 'WildStorm', 'Wildstorm', 'wildstorm', 'Wonder Comics', 'Young Animal', 'Zuda Comics']
        if self.publisher in Marvel:
            self.imprint = self.publisher
            self.publisher = 'Marvel'

        if self.publisher in DC_Comics:
            self.imprint = self.publisher
            self.publisher = 'DC Comics'
