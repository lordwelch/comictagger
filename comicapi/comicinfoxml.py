"""A class to encapsulate ComicRack's ComicInfo.xml data"""

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

import xml.etree.ElementTree as ET
#from datetime import datetime
#from pprint import pprint
#import zipfile

from .genericmetadata import GenericMetadata
from .issuestring import IssueString
from . import utils


class ComicInfoXml:

    writer_synonyms = ['writer', 'plotter', 'scripter']
    penciller_synonyms = ['artist', 'penciller', 'penciler', 'breakdowns']
    inker_synonyms = ['inker', 'artist', 'finishes']
    colorist_synonyms = ['colorist', 'colourist', 'colorer', 'colourer']
    letterer_synonyms = ['letterer']
    cover_synonyms = ['cover', 'covers', 'coverartist', 'cover artist']
    editor_synonyms = ['editor']

    def getParseableCredits(self):
        parsable_credits = []
        parsable_credits.extend(self.writer_synonyms)
        parsable_credits.extend(self.penciller_synonyms)
        parsable_credits.extend(self.inker_synonyms)
        parsable_credits.extend(self.colorist_synonyms)
        parsable_credits.extend(self.letterer_synonyms)
        parsable_credits.extend(self.cover_synonyms)
        parsable_credits.extend(self.editor_synonyms)
        return parsable_credits

    def metadataFromString(self, string):

        tree = ET.ElementTree(ET.fromstring(string))
        return self.convertXMLToMetadata(tree)

    def stringFromMetadata(self, metadata):

        header = '<?xml version="1.0"?>\n'

        tree = self.convertMetadataToXML(self, metadata)
        tree_str = ET.tostring(tree.getroot()).decode()
        return header + tree_str

    def indent(self, elem, level=0):
        # for making the XML output readable
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def convertMetadataToXML(self, filename, metadata):

        # shorthand for the metadata
        md = metadata

        # build a tree structure
        root = ET.Element("ComicInfo")
        root.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"
        root.attrib['xmlns:xsd'] = "http://www.w3.org/2001/XMLSchema"
        # helper func

        def assign(cix_entry, md_entry):
            if md_entry is not None:
                ET.SubElement(root, cix_entry).text = "{0}".format(md_entry)

        assign('Title', md.title)
        assign('Series', md.series)
        assign('Number', IssueString(md.issue).asString())
        assign('Count', utils.xlate(md.issueCount, True))
        assign('Volume', utils.xlate(md.volume, True))
        assign('AlternateSeries', md.alternateSeries)
        assign('AlternateNumber', IssueString(md.alternateNumber).asString())
        assign('StoryArc', md.storyArc)
        assign('SeriesGroup', md.seriesGroup)
        assign('AlternateCount', md.alternateCount.lstrip("0"))
        assign('Summary', md.comments)
        assign('Notes', md.notes)
        assign('Year', utils.xlate(md.year, True))
        assign('SeriesYear', utils.xlate(md.seriesYear, True))
        assign('Month', utils.xlate(md.month, True))
        assign('Day', utils.xlate(md.day, True))

        # need to specially process the credits, since they are structured
        # differently than CIX
        credit_writer_list = list()
        credit_penciller_list = list()
        credit_inker_list = list()
        credit_colorist_list = list()
        credit_letterer_list = list()
        credit_cover_list = list()
        credit_editor_list = list()

        # first, loop thru credits, and build a list for each role that CIX
        # supports
        for credit in metadata.credits:

            if credit['role'].lower() in set(self.writer_synonyms):
                credit_writer_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.penciller_synonyms):
                credit_penciller_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.inker_synonyms):
                credit_inker_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.colorist_synonyms):
                credit_colorist_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.letterer_synonyms):
                credit_letterer_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.cover_synonyms):
                credit_cover_list.append(credit['person'].replace(",", ""))

            if credit['role'].lower() in set(self.editor_synonyms):
                credit_editor_list.append(credit['person'].replace(",", ""))

        # second, convert each list to string, and add to XML struct
        if len(credit_writer_list) > 0:
            node = ET.SubElement(root, 'Writer')
            node.text = utils.listToString(credit_writer_list)

        if len(credit_penciller_list) > 0:
            node = ET.SubElement(root, 'Penciller')
            node.text = utils.listToString(credit_penciller_list)

        if len(credit_inker_list) > 0:
            node = ET.SubElement(root, 'Inker')
            node.text = utils.listToString(credit_inker_list)

        if len(credit_colorist_list) > 0:
            node = ET.SubElement(root, 'Colorist')
            node.text = utils.listToString(credit_colorist_list)

        if len(credit_letterer_list) > 0:
            node = ET.SubElement(root, 'Letterer')
            node.text = utils.listToString(credit_letterer_list)

        if len(credit_cover_list) > 0:
            node = ET.SubElement(root, 'CoverArtist')
            node.text = utils.listToString(credit_cover_list)

        if len(credit_editor_list) > 0:
            node = ET.SubElement(root, 'Editor')
            node.text = utils.listToString(credit_editor_list)

        assign('Publisher', md.publisher)
        assign('Imprint', md.imprint)
        assign('Genre', md.genre)
        assign('Web', md.webLink)
        assign('PageCount', md.pageCount)
        assign('LanguageISO', md.language)
        assign('Format', md.format)
        assign('AgeRating', md.maturityRating)
        if md.blackAndWhite is not None and md.blackAndWhite:
            ET.SubElement(root, 'BlackAndWhite').text = "Yes"
        assign('Manga', md.manga)
        assign('Characters', md.characters)
        assign('Teams', md.teams)
        assign('Locations', md.locations)
        assign('ScanInformation', md.scanInfo)

        #  loop and add the page entries under pages node
        if len(md.pages) > 0:
            pages_node = ET.SubElement(root, 'Pages')
            for page_dict in md.pages:
                page_node = ET.SubElement(pages_node, 'Page')
                page_node.attrib = page_dict

        # self pretty-print
        self.indent(root)

        # wrap it in an ElementTree instance, and save as XML
        tree = ET.ElementTree(root)
        return tree

    def convertXMLToMetadata(self, tree):

        root = tree.getroot()

        if root.tag != 'ComicInfo':
            raise 1
            return None

        def get(name):
            tag = root.find(name)
            if tag is None:
                return ""
            return tag.text

        metadata = GenericMetadata()

        metadata.series = utils.xlate(get('Series'))
        metadata.title = utils.xlate(get('Title'))
        metadata.issue = IssueString(utils.xlate(get('Number'))).asString()
        metadata.issueCount = utils.xlate(get('Count'), True)
        metadata.volume = utils.xlate(get('Volume'), True)
        metadata.alternateSeries = utils.xlate(get('AlternateSeries'))
        metadata.alternateNumber = IssueString(utils.xlate(get('AlternateNumber'))).asString()
        metadata.alternateCount = utils.xlate(get('AlternateCount'), True)
        metadata.comments = utils.xlate(get('Summary'))
        metadata.notes = utils.xlate(get('Notes'))
        metadata.year = utils.xlate(get('Year'), True)
        metadata.seriesYear = utils.xlate(get('SeriesYear'), True)
        metadata.month = utils.xlate(get('Month'), True)
        metadata.day = utils.xlate(get('Day'), True)
        metadata.publisher = utils.xlate(get('Publisher'))
        metadata.imprint = utils.xlate(get('Imprint'))
        metadata.genre = utils.xlate(get('Genre'))
        metadata.webLink = utils.xlate(get('Web'))
        metadata.language = utils.xlate(get('LanguageISO'))
        metadata.format = utils.xlate(get('Format'))
        metadata.manga = utils.xlate(get('Manga'))
        metadata.characters = utils.xlate(get('Characters'))
        metadata.teams = utils.xlate(get('Teams'))
        metadata.locations = utils.xlate(get('Locations'))
        metadata.pageCount = utils.xlate(get('PageCount'))
        metadata.scanInfo = utils.xlate(get('ScanInformation'))
        metadata.storyArc = utils.xlate(get('StoryArc'))
        metadata.seriesGroup = utils.xlate(get('SeriesGroup'))
        metadata.maturityRating = utils.xlate(get('AgeRating'))

        tmp = utils.xlate(get('BlackAndWhite'))
        metadata.blackAndWhite = False
        if tmp is not None and tmp.lower() in ["yes", "true", "1"]:
            metadata.blackAndWhite = True
        # Now extract the credit info
        for n in root:
            if (n.tag == 'Writer' or
                n.tag == 'Penciller' or
                n.tag == 'Inker' or
                n.tag == 'Colorist' or
                n.tag == 'Letterer' or
                n.tag == 'Editor'
                ):
                if n.text is not None:
                    for name in n.text.split(','):
                        metadata.addCredit(name.strip(), n.tag)

            if n.tag == 'CoverArtist':
                if n.text is not None:
                    for name in n.text.split(','):
                        metadata.addCredit(name.strip(), "Cover")

        # parse page data now
        pages_node = root.find("Pages")
        if pages_node is not None:
            for page in pages_node:
                metadata.pages.append(page.attrib)
                # print page.attrib

        metadata.isEmpty = False

        return metadata

    def writeToExternalFile(self, filename, metadata):

        tree = self.convertMetadataToXML(self, metadata)
        # ET.dump(tree)
        tree.write(filename, encoding='utf-8')

    def readFromExternalFile(self, filename):

        tree = ET.parse(filename)
        return self.convertXMLToMetadata(tree)
