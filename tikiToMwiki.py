#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Convert TikiWiki content to MediaWiki content.
#
# Code taken from
# https://www.mediawiki.org/w/index.php?title=Manual:TikiWiki_Conversion
#
# and commit history extracted from this wiki page's revision history with
# all available information.
#
# Code was originally developed by Rosie Clarkson, Chris Eveleigh
# <development@planningportal.gov.uk> under the © Crown copyright 2008 for the
# Planning Portal. All later developments as far as documented in the
# original revision history is inserted in the commit history of this
# repository.
#
# © copyright PTB 2018, T. Bruns, B.Ludwig

import html.entities as htmlentitydefs
import io
import re
import sys
import tarfile
import time
from email.parser import Parser
from html.parser import HTMLParser
from optparse import OptionParser
from urllib.parse import quote, unquote, urljoin
from xml.sax.saxutils import unescape, escape

from defusedxml import minidom

# add any other links you may want to map between wikis here
url_maps = {'http://tikiwiki.org/RFCWiki':
            'http://meta.wikimedia.org/wiki/Cheatsheet'}


# checks for HTML tags
class HTMLChecker(HTMLParser):
    # HTMLChecker actually should implement the abstract method
    # _markupbase.ParserBase.error() which we don't do because the method is
    # kind of deprecated since Python 3.5 (see
    # https://bugs.python.org/issue31844)

    def handle_starttag(self, tag, attrs):
        global validate
        validate = True
        return True

    def handle_endtag(self, tag):
        global validate
        return True


# MediaWiki relies on having the right number of new lines between syntax -
# for example having two new lines in a list starts a new list. The elements
# that do/don't start a new line in HTML can be controlled by the CSS. The
# CSS used depends on which skin you're using.
class HTMLToMwiki(HTMLParser):
    global wikitext
    global sourceurl
    global pages
    global uploads
    global headings
    # if the parser is within a link
    link = False
    src = ''
    innowiki = False
    # if the parser is within italics
    inem = False
    # if the parser is within bold
    instrong = False
    # if the parser is within a heading
    inheading = False
    # whether the parser is within an ordered list (is numeric to deal with
    # nested lists)
    list = 0
    # whether the parser is within a list item - in order to deal with <p>
    # and <br/> tags in ways that wont break it
    litem = 0
    # the number of ul tags used for nested lists
    ul_count = 0
    # the number of ol tags used for nested lists
    ol_count = 0
    col_count = 0

    def handle_starttag(self, tag, attrs):
        if self.innowiki:
            complete_tag = '<' + tag
            for attr in attrs:
                complete_tag += ' ' + attr[0] + '="' + attr[1] + '"'
            wikitext.append(complete_tag + '>')
        else:
            if tag == 'nowiki':
                wikitext.append('<nowiki>')
                self.innowiki = True
            if tag == 'a':
                self.src = ''
                for att in attrs:
                    if att[0] == 'href':
                        self.src = att[1]
                if self.src in url_maps:
                    self.src = url_maps[self.src]
                # deals with uploads
                if 'tiki-download_file.php' in self.src:
                    uploads.append(self.src)
                self.link = True
            if tag == 'ol':
                self.ol_count += 1
                self.list += 1

            if tag == 'ul':
                self.ul_count += 1
            if tag == 'li':
                # append the right no. of # or *s according to the level of
                # nesting
                self.litem += 1
                if self.list > 0:
                    wikitext.append('\n' + ('#' * self.ol_count))
                else:
                    wikitext.append('\n' + ('*' * self.ul_count))
            if tag == 'img':
                src = ''
                for att in attrs:
                    if att[0] == 'src':
                        src = att[1]
                src = quote(src)
                # we have several different ways of specifying image sources
                # in our TikiWiki
                imagepath = urljoin(sourceurl, src)
                if options.newImagepath != '':
                    imagepath = urljoin(
                        options.newImagepath, src.split('/')[-1])
                # the pic tag is used later to identify this as a picture and
                # process the correct MediaWiki syntax
                wikitext.append('<pic>' + imagepath + ' ')
            if tag == 'table':
                wikitext.append('\n{|')
                for att in attrs:
                    # table formatting
                    wikitext.append(' ' + att[0] + '="' + att[1] + '"')
            if tag == 'tr':
                wikitext.append('\n|-')
                self.col_count = 0
            if tag == 'td':
                self.col_count += 1
                if self.col_count > 1:
                    wikitext.append('\n||')
                else:
                    wikitext.append('\n|')
            if tag == 'caption':
                wikitext.append('\n|+')
            if tag in ('strong', 'b'):
                self.instrong = True
                wikitext.append("'''")
            if tag in ('em', 'i'):
                self.inem = True
                wikitext.append("''")
            if tag == 'p':
                # new lines in the middle of lists break the list so we have
                # to use the break tag
                if self.litem == 0:
                    br = '\n'
                else:
                    br = '<br/>'
                # newlines in the middle of formatted text break the
                # formatting so we have to end and restart the formatting
                # around the new lines
                if self.inem:
                    br = "''" + br + br + "''"
                if self.instrong:
                    br = "'''" + br + br + "'''"
                wikitext.append(br)
            if tag == 'h1':
                self.inheading = True
                # headings must start on a new line
                wikitext.append('\n\n==')
                headings.append(tag)
            if tag == 'h2':
                self.inheading = True
                wikitext.append('\n\n===')
                headings.append(tag)
            if tag == 'h3':
                self.inheading = True
                wikitext.append('\n\n====')
                headings.append(tag)
            else:
                wikitext.append('<' + tag + '>')

    def handle_endtag(self, tag):
        if tag == 'nowiki':
            wikitext.append('</nowiki>')
            self.innowiki = False
        if not self.innowiki:
            if self.link:
                self.src = ''
                self.link = False
            if tag == 'img':
                wikitext.append('</pic>')
            if tag == 'ol':
                self.ol_count -= 1
                self.list -= 1
                wikitext.append('\n\n')
            if tag == 'ul':
                self.ul_count -= 1
                wikitext.append('\n\n')
            if tag == 'li':
                self.litem -= 1
            if tag == 'table':
                wikitext.append('\n\n|}')
            if tag in ('strong', 'b'):
                self.instrong = False
                wikitext.append("'''")
            if tag in ('em', 'i'):
                self.inem = False
                wikitext.append("''")
            if tag == 'h1':
                self.inheading = False
                wikitext.append('==\n\n')
            if tag == 'h2':
                self.inheading = False
                wikitext.append('===\n\n')
            if tag == 'h3':
                self.inheading = False
                wikitext.append('====\n\n')
            if tag == 'p':
                if self.inheading:
                    br = ''
                elif self.litem == 0:
                    br = '\n'
                else:
                    br = '<br/>'
                if self.inem:
                    br = " ''" + br + "''"
                if self.instrong:
                    br = " '''" + br + "'''"
                wikitext.append(br)
            if tag == 'br':
                if self.inheading:
                    br = ''
                elif self.litem == 0:
                    br = '\n'
                else:
                    br = '<br/>'
                if self.inem:
                    br = " ''" + br + "''"
                if self.instrong:
                    br = " '''" + br + "'''"
                wikitext.append(br)
            if tag == 'hr':
                wikitext.append('\n----\n')
            else:
                wikitext.append('</' + tag + '>')
        else:
            wikitext.append('</' + tag + '>')

    # check for symbols which are MediaWiki syntax when at the start of a line
    @staticmethod
    def check_append(data):
        stripped = data.lstrip()
        for symbol in ('----', '*', '#', '{|', '==', '===', '===='):
            if stripped.startswith(symbol):
                if len(wikitext) > 2 and wikitext[-3] == '\n':
                    if not symbol.startswith('='):
                        data = '<nowiki>' + symbol + '</nowiki>' \
                               + stripped[len(symbol):]
                    else:
                        if data.find(symbol, len(symbol)):
                            data = '<nowiki>' + symbol + '</nowiki>' \
                                   + stripped[len(symbol):]
        return data

    def handle_data(self, data):
        if self.link:
            # sometimes spaces are in the piped data (probably because of our
            # editor) so we need to make sure we add that before the link
            space = ''
            if data.startswith(' '):
                space = ' '
            if self.src.startswith(sourceurl + 'tiki-download_file.php'):
                wikitext.append(space + '[' + self.src + ' ' + data + ']')
            elif self.src.startswith(sourceurl):
                if 'page=' in self.src:
                    ptitle = self.src.split('page=')
                    pagename = ptitle[1].replace('+', ' ')
                    for file in pages:
                        # MediaWiki is case sensitive to page names and
                        # TikiWiki isn't so check that the file actually exists
                        if file.lower() == pagename.lower():
                            pagename = file
                    wikitext.append(space + '[[' + pagename + '|' + data
                                    + ']]')
            else:
                # catch relative urls
                if self.src.startswith('..'):
                    self.src = urljoin(sourceurl, self.src)
                wikitext.append(space + '[' + self.src + ' ' + data + ']')
        elif self.litem:
            # if we're in a list put nowiki tags around data beginning with *
            # or # so it isn't counted as nesting
            if data[0] in ('*', '#'):
                data = '<nowiki>' + data[0] + '</nowiki>' + data[1:]
            wikitext.append(data)
        else:
            data = self.check_append(data)
            wikitext.append(data)

    def handle_entityref(self, name):
        name = "&amp;" + name + ";"
        if self.link:
            wikitext.append(' ' + name)
        elif self.litem:
            wikitext.append(name)
        else:
            wikitext.append(name)

    def handle_charref(self, name):
        name = "&amp;" + name + ";"
        if self.link:
            wikitext.append(' ' + name)
        elif self.litem:
            wikitext.append(name)
        else:
            wikitext.append(name)


def insert_image(word):
    global image
    global imagenames
    global imageids
    # there are even more ways to specify pic sources in our TikiWiki
    if 'name=' in word:
        parts = word.split('=')
        try:
            filename = imagenames[parts[2]]
        except KeyError:
            sys.stderr.write(parts[2] + 'doesn\'t exist in your image XML file '
                                        'and won\'t be displayed properly\n')
            filename = parts[2]
        filename = quote(filename)
        imagepath = urljoin(urljoin(sourceurl, imageurl), filename)
        if options.newImagepath != '':
            imagepath = urljoin(options.newImagepath, filename)
        words.append('<pic>' + imagepath)
    if 'id=' in word:
        parts = word.split('=')
        try:
            filename = imageids[parts[2]]
            if options.verbose_mode:
                sys.stdout.write(
                    'The attachment with ID ' + parts[2]
                    + ' was successfully added to revision ' + str(partcount)
                    + ' of the page "' + title + '"\n')
        except KeyError:
            sys.stderr.write('The image with ID ' + parts[
                2] + ' doesn\'t exist in your image XML file and won\'t be '
                     'displayed properly\n')
            filename = parts[2]
        filename = quote(filename)
        imagepath = urljoin(urljoin(sourceurl, imageurl), filename)
        if options.newImagepath != '':
            imagepath = urljoin(options.newImagepath, filename)
        words.append('<pic>' + imagepath)
    if '}' in word:
        bracket = word.find('}')
        if word[-1] != '}':
            if word[bracket + 1] != ' ':
                word = word.replace('}', '</pic> ')
            else:
                word = word.replace('}', '</pic>')
        word = word.replace('}', '</pic>')
        words.append(word)
        image = False

    return words


def insert_link(word):
    global intLink
    global page
    global words
    global pages
    # the link may be split if it contains spaces so it may be sent in parts
    brackets = word.find('((')
    if brackets != -1:
        word = word.replace('((', '[[')
        page = word[brackets:]
        words.append(word[:brackets])
        if '))' in word:
            word = word.replace('))', ']]')
            last_pos = word.find(']]')
            text = word[brackets + 2:last_pos]
            # again check the filenames to ensure case sensitivity is ok
            for file in pages:
                if file.encode("Latin-1").lower() \
                        == text.lower():
                    text = file
            text = '[[' + text + word[last_pos:]
            if text[-1] != '\n':
                words.append(text + ' ')
            else:
                words.append(text)
            page = ''
            intLink = False

    elif '))' in word:
        word = word.replace('))', ']]')
        page += ' ' + word
        pipe = page.find('|')
        if pipe != -1:
            last_pos = pipe
            text = page[2:pipe]
        else:
            brackets = page.find(']]')
            last_pos = brackets
            text = page[2:brackets]
        for file in pages:
            if file.encode("latin-1").lower() == text.lower():
                page = page[:2] + file + page[last_pos:]
        if page[-1] != '\n':
            words.append(page + ' ')
        else:
            words.append(page)
        page = ''
        intLink = False
    else:
        page += ' ' + word


parser = OptionParser()
parser.add_option("-n", "--notableofcontents", action="store_true",
                  dest="notoc", default=False,
                  help="disable all automatic contents tables")
parser.add_option("-m", "--maxfilesize", action="store", type="int",
                  dest="max", default=1, help="the maximum import file size")
parser.add_option("-j", "--newimageurl", action="store", type="string",
                  dest="newImagepath", default='',
                  help="the new location of any images (inc. trailing slash)")
parser.add_option("-i", "--imageurl", action="store", type="string",
                  dest="imageurl", default='',
                  help="the relative URL used in tiki to access images (inc. "
                       "trailing slash)")
parser.add_option("-p", "--privatepages", action="store", type="string",
                  dest="privatexml", default='',
                  help="an XML file containing any private pages not to be "
                       "added to the wiki")
parser.add_option("-o", "--outputfile", action="store", type="string",
                  dest="outputfile", default='',
                  help="the name of the output wiki XML file(s)")
parser.add_option("-k", "--imagexml", action="store", type="string",
                  dest="imagexml", default='',
                  help="an XML file containing metadata for the images in the "
                       "tiki")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose_mode",
                  default=False,
                  help="enable reporting to stdout about attachment conversion")

(options, args) = parser.parse_args()

# The tar file containing the TikiWiki file export - if not specified read from
# stdin. stdin doesn't work at the moment and fails after you've used
# extractfile as this returns nothing
if len(args) > 1:
    archive = tarfile.open(args[1])
    # add all files in the export tar to the list of pages
    pages = archive.getnames()
    if options.outputfile == '':
        outputfile = args[1].replace('.tar', '.xml')
    else:
        outputfile = options.outputfile
else:
    pages = []
    # if reading from stdin you can't iterate through the files again so
    # pages is left empty and links are not corrected
    archive = tarfile.open(name=sys.stdin.name, mode='r|', fileobj=sys.stdin)
    # if you're reading from stdin and don't specify an output file output to
    # stdout
    if options.outputfile == '':
        options.outputfile = '-'
    outputfile = options.outputfile
p = Parser()

# Open the output channel by either setting `stdout` or opening a file.
if options.outputfile == '-':
    mwikixml = sys.stdout
else:
    mwikixml = open(outputfile, 'w', encoding='utf-8')
    sys.stdout.write('Creating new wiki xml file ' + outputfile)

# the source URL of the TikiWiki - in the form http://[your url]/tiki/
sourceurl = args[0]

# the relative address used to access pictures in TikiWiki
imageurl = options.imageurl

privatePages = []
if options.privatexml != '':
    privateparse = minidom.parse(options.privatexml)
    rows = privateparse.getElementsByTagName('row')
    for row in rows:
        fields = row.getElementsByTagName('field')
        for field in fields:
            if field.getAttribute('name') == 'pageName':
                privatePages.append(field.firstChild.data)
# fill the lookup table with the image information
# a file containing an xml dump from the TikiWiki DB
imagenames = {}
imageids = {}
if options.imagexml != '':
    imagexml = options.imagexml
    lookup = minidom.parse(imagexml)

    rows = lookup.getElementsByTagName('row')
    for row in rows:
        fields = row.getElementsByTagName('field')
        for field in fields:
            if field.getAttribute('name') == 'name':
                iname = field
            if field.getAttribute('name') == 'filename':
                ifile = field
            if field.getAttribute('name') == 'imageID':
                iid = field
        imagenames[iname.firstChild.data] = ifile.firstChild.data
        imageids[iid.firstChild.data] = ifile.firstChild.data

# list of users who have edited pages
authors = []
filepages = {}
pagecount = 0
versioncount = 0

# Start writing to the specified output.
mwikixml.write('<mediawiki xml:lang="en">\n')
header = '<siteinfo>\n' \
         '<base>' + sourceurl + '</base>\n' \
                                '</siteinfo>\n'
mwikixml.write(header)

for member in archive:
    if member.name not in privatePages:
        # add each file in the TikiWiki export directory
        tikifile = io.TextIOWrapper(
            archive.extractfile(member), encoding='utf-8')
        mimefile = p.parse(tikifile)
        mwikixml.write('<page>\n')
        partcount = 0
        uploads = []
        revisions = []

        if not mimefile.is_multipart():
            partcount = 1
        for part in mimefile.walk():
            revision = ''
            if partcount == 1:
                title = unquote(part.get_param('pagename'))
                mwikixml.write(('<title>' + title + '</title>\n'))
            partcount += 1
            if part.get_params() is not None and \
                    ('application/x-tikiwiki', '') in part.get_params():
                versioncount += 1
                headings = []
                if part.get_param('lastmodified') is None:
                    break
                revision += '<revision>\n'
                revision += '<id>REV_ID_PLACEHOLDER</id>\n'
                revision += '<timestamp>' + time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ', time.gmtime(eval(part.get_param(
                        'lastmodified')))) + '</timestamp>\n'
                revision += '<contributor><username>' + part.get_param(
                    'author') + '</username></contributor>\n'
                # add author to list of contributors to be output at the end
                if part.get_param('author') not in authors:
                    authors.append(part.get_param('author'))
                revision += '<text xml:space="preserve">\n'
                mwiki = ''
                # we add the TikiWiki description to the page in bold and
                # italic (much as it was in TikiWiki ) for them to function
                # properly we need to ensure that these strings are followed
                # by a new line the </br> is used as a placeholder and is
                # converted to \n later
                if part.get_param('description') not in (None, ''):
                    mwiki += "'''''" + unquote(part.get_param('description')) \
                             + "'''''</br>"
                # then add the table of contents (or specify none)
                if options.notoc:
                    mwiki = mwiki + "__NOTOC__</br>"
                else:
                    mwiki += "__TOC__</br>"
                mwiki += part.get_payload()

                # does the validator do anything?!
                validate = False
                validator = HTMLChecker()
                validator.feed(mwiki)
                # fixes pages that end up on a single line (these were
                # probably created by our WYSIWYG editor being used on windows
                # and linux)
                if not validate:
                    mwiki = mwiki.replace('\t', '    ')
                    mwiki = mwiki.replace('  ', ' &nbsp;')
                    mwiki = mwiki.replace('<', '&lt;')
                    mwiki = mwiki.replace('>', '&gt;')

                    # make sure newlines after headings are preserved
                    next_elem = 0
                    while '\r\n!' in mwiki[next_elem:] or '&lt;/br&gt;!' in \
                            mwiki[next_elem:] or mwiki[
                                                 next_elem:].startswith('!'):
                        if mwiki[next_elem:].startswith('!'):
                            found = next_elem
                        else:
                            foundreturn = mwiki.find('\r\n!', next_elem)
                            foundbreak = mwiki.find('&lt;/br&gt;!', next_elem)
                            if (foundreturn != -1 and foundreturn <
                                    foundbreak) or foundbreak == -1:
                                found = foundreturn + 2
                            else:
                                found = foundbreak + 11

                        next_elem = mwiki.find('\r\n', found)
                        if next_elem == -1:
                            break
                        mwiki = mwiki[:next_elem] + '</br>' + mwiki[next_elem
                                                                    + 2:]
                        next_elem += 5

                    # as validate is false the page does not contain any html
                    # so whitespace needs to be preserved
                    mwiki = mwiki.replace('\r\n', '</br>')

                # double escape < and > entities so that &lt; is not
                # unescaped to < which is then treated as HTML tags
                mwiki = mwiki.replace('&amp;lt;', '&amp;amp;lt;')
                mwiki = mwiki.replace('&amp;gt;', '&amp;amp;gt;')
                mwiki = mwiki.replace('&lt;', '&amp;lt;')
                mwiki = mwiki.replace('&gt;', '&amp;gt;')
                mwiki = mwiki.replace(u'\ufffd', '&nbsp;')

                # unescape XML entities
                entitydefs = dict(("&" + k + ";", chr(v)) for k, v in
                                  htmlentitydefs.name2codepoint.items())
                entitydefs.pop("&amp;")
                entitydefs.pop("&gt;")
                entitydefs.pop("&lt;")
                mwiki = unescape(mwiki, entitydefs)

                # replace TikiWiki syntax that will be interpreted badly with
                # TikiWiki syntax the parser will understand empty formatting
                # tags will be converted to many "'"s which then confuses
                # MediaWiki
                mwiki = mwiki.replace('[[', '~np~[~/np~')
                # need to replace no wiki tags here in case any html/xml is
                # inside them that we want to keep
                mwiki = mwiki.replace('~np~', '<nowiki>')
                mwiki = mwiki.replace('~/np~', '</nowiki>')
                mwiki = mwiki.replace('<em></em>', '')
                mwiki = mwiki.replace('<em><em>', '<em>')
                mwiki = mwiki.replace('</em></em>', '</em>')
                mwiki = mwiki.replace('<strong></strong>', '')
                mwiki = mwiki.replace('<strong><strong>', '<strong>')
                mwiki = mwiki.replace('</strong></strong>', '</strong>')
                # this makes sure definitions keep their preceding newline
                mwiki = mwiki.replace('\n;', '</br>;')
                mwiki = mwiki.replace('</br>', '\n')
                mwiki = mwiki.replace('&lt;/br&gt;', '\n')
                mwiki = mwiki.replace('\r', ' ')
                mwiki = mwiki.replace('\t', ' ')

                # Mediawiki automatically creates a table of content
                mwiki = mwiki.replace('Table of content', '')
                mwiki = mwiki.replace('{maketoc}', '')

                # convert === underline syntax before the html converter as
                # headings in MediaWiki use =s and h3 tags will become
                # ===heading===
                next_elem = 0
                while '===' in mwiki[next_elem:]:
                    start = mwiki.find('===', next_elem)
                    end = mwiki.find('===', start + 3)

                    if end != -1:
                        mwiki = mwiki[:start] + '<u>' + mwiki[start + 3:end] \
                                + '</u>' + mwiki[end + 3:]
                    next_elem = start + 1
                # if there is another === convert them both

                # print mwiki

                wikitext = []

                # convert any HTML tags to MediaWiki syntax
                htmlConverter = HTMLToMwiki()
                htmlConverter.feed(mwiki)

                mwiki = ''.join(wikitext)

                # replace TikiWiki syntax with MediaWiki
                mwiki = mwiki.replace('__', "'''")

                # split the text into lines and then strings to parse
                words = []
                image = False
                intLink = False
                box = False
                colour = False
                inColourTag = False
                inFormula = False
                page = ''
                centre = False
                for line in mwiki.splitlines(True):
                    # Convert external links to MediaWiki syntax
                    m = re.match(r'(.*)\[(.*)\|(.*)\](.*)', line)
                    if m:
                        line = m.group(1) + "[" + re.sub(
                            r'(.*)&amp;(.*);('r'.*)', r'\1&\2\3', m.group(2)) \
                               + " " + m.group(3) + "]" + m.group(4) + "\n"

                    # Convert 'CODE' samples to MediaWiki syntax
                    line = re.sub(r'{CODE\(caption=&amp;gt;(.*)\)}',
                                  r'<!-- \1 --><source>', line)
                    line = re.sub(r'{CODE\((.*)\)}',
                                  r'<source>', line)
                    line = re.sub(r'{CODE}', r'</source>', line)

                    # Convert anchor
                    line = re.sub(r'{ANAME\(\)}(.*){ANAME}',
                                  r'<span id=&quot;\1&quot;></span>', line)
                    # Convert anchor links
                    line = re.sub(r'{ALINK\(aname=(?:")?([^"]*)(?:")?\)}('
                                  r'.*){ALINK}', r'[[#\1|\2]]', line)

                    heading = False
                    noCentre = False

                    # Handle formulas
                    # Convert formulas to XWiki syntax:
                    # {{formula &#124; a(t) &#124; fontsize=SMALLER}}
                    # which represents a MediaWiki tag 'formula' with
                    # parameter 'fontsize' set to 'SMALLER' and encapsulating
                    # 'a(t)'. An important addition to the algorithm will be
                    # to add a replacement of '=' by '\equal' because
                    # otherwise '=' breaks the formula. TODO This actually does
                    # not allow for inline formulas anymore, so we need a
                    # solution based on the Extension MathJax
                    if re.search(r'{HTML\(\)}', line):
                        inFormula = True
                        line = re.sub(r'{HTML\(\)}\\[(,\[]',
                                      r'{{formula |', line)
                        line = re.sub(r'{HTML\(\)}', '{{formula |;', line)
                        line = re.sub(r'\\[(,\[]', '', line)
                    if inFormula:
                        line = re.sub(r'\\varphi', r'\\phi', line)
                        line = line.replace('=', '\equal')
                    if re.search(r'{HTML}', line):
                        inFormula = False
                        line = re.sub(r'\\[),\]]{HTML}',
                                      r'| fontsize=SMALLER}}', line)
                        line = re.sub(r'{HTML}', r'| fontsize=SMALLER}}', line)


                    # if there are an odd no. of ::s don't convert to
                    # centered text
                    if line.count('::') % 2 != 0:
                        noCentre = True
                    count = 0
                    spl = line.split(' ')
                    if spl[0].find('!') == 0:
                        heading = True
                    for elem in spl:
                        # handle headings
                        if heading is True:
                            if count is 0 and elem:
                                # replace !s
                                bangs = 0
                                while elem[bangs] == '!':
                                    elem = elem.replace('!', '=', 1)
                                    bangs += 1
                                    if bangs >= len(elem):
                                        if len(spl) == 1:
                                            bangs /= 2
                                        break
                            if count is len(spl) - 1:
                                # add =s to end
                                end = elem.find('\n')
                                if end != -1:
                                    elem = elem[:end] + (bangs * '=') + elem[
                                                                        end:]
                                else:
                                    elem = elem[:end] + (bangs * '=')
                        # handle centered text
                        if '::' in elem and not noCentre:
                            next_elem = 0
                            while '::' in elem[next_elem:]:
                                next_elem = elem.find('::')
                                if centre:
                                    centre = False
                                    elem = elem.replace('::', '</center>', 1)
                                else:
                                    centre = True
                                    elem = elem.replace('::', '<center>', 1)
                        # handle font colours
                        if inColourTag:
                            colon = elem.find(':')
                            if colon != -1:
                                elem = elem[:colon] + '">' + elem[colon + 1:]
                                inColourTag = False
                        if '~~' in elem:
                            next_elem = 0
                            while '~~' in elem[next_elem:]:
                                next_elem = elem.find('~~')
                                if colour:
                                    # end span
                                    colour = False
                                    elem = elem.replace('~~', '</span>', 1)
                                else:
                                    # start span
                                    colour = True
                                    colon = elem.find(':', next_elem)
                                    extratext = ''
                                    if colon != -1:
                                        elem = elem[:next_elem] \
                                               + "<span style='color:" \
                                               + elem[next_elem + 2:colon] \
                                               + "'>" + elem[colon + 1:]
                                    else:
                                        elem = elem[:next_elem] \
                                               + '<span style="color:' \
                                               + elem[next_elem + 2:]
                                        inColourTag = True
                                next_elem += 1
                        if '{img' in elem:
                            image = True
                        if '((' in elem:
                            intLink = True
                        if image:
                            words = insert_image(elem)
                        elif intLink:
                            insert_link(elem)
                        else:
                            # stops MediaWiki automatically creating links (
                            # which can then be broken by formatting
                            if ('http' in elem or 'ftp://' in elem) and '[' \
                                    not in elem and ']' not in elem and \
                                    '<pic>' not in elem and '<pre>' not in \
                                    elem and '</pre>' not in elem and not box:
                                index = 0
                                do_format = False
                                formatted = ''
                                for char in elem:
                                    index += 1
                                    if char == "'":
                                        if not do_format:
                                            do_format = True
                                            formatted = formatted + '</nowiki>'
                                    else:
                                        if do_format:
                                            do_format = False
                                            formatted = formatted + '<nowiki>'

                                    formatted += char

                                elem = '<nowiki>' + formatted + '</nowiki>'
                            if elem != '':
                                if '\n' in elem[-1]:
                                    words.append(elem)
                                else:
                                    words.append(elem + ' ')
                        count += 1

                mwiki = ''.join(words)
                # get rid of pic placeholder tags
                mwiki = mwiki.replace("<pic>", "")
                mwiki = mwiki.replace("</pic>", "")

                # make sure there are no single newlines - MediaWiki just
                # ignores them. Replace multiple lines with single and then
                # single with double.
                while "\n \n" in mwiki:
                    mwiki = mwiki.replace("\n \n", "\n")
                while "\n\n" in mwiki:
                    mwiki = mwiki.replace("\n\n", "\n")
                mwiki = mwiki.replace('\n', '\n\n')

                # Add one space to bullet points.
                mwiki = mwiki.replace('\n*', '\n* ')

                # replace multiple lines with single where they would break
                # formatting - such as in a list
                mwiki = mwiki.replace('\n\n#', '\n#')
                mwiki = mwiki.replace('\n\n*', '\n*')
                mwiki = mwiki.replace('*<br/>', '*')
                mwiki = mwiki.replace('#<br/>', '#')
                mwiki = mwiki.lstrip('\n')

                lines = []
                for line in mwiki.splitlines(True):
                    if line.startswith(':'):
                        line = '<nowiki>:</nowiki>' + line[1:]
                    lines.append(line)
                mwiki = ''.join(lines)

                entitydefs = dict((chr(k), "&amp;" + v + ";") for k, v in
                                  htmlentitydefs.codepoint2name.items())
                entitydefs.pop('<')
                entitydefs.pop('>')
                entitydefs.pop('&')
                entitydefs['|'] = '&#124;'
                mwiki = escape(mwiki, entitydefs)

                for index, value in enumerate(mwiki):
                    if value < " " and value != '\n' and value != \
                            '\r' and value != '\t':
                        mwiki = mwiki[:index] + "?" + mwiki[index + 1:]

                mwiki = mwiki.replace('amp;lt;', 'lt;')
                mwiki = mwiki.replace('amp;gt;', 'gt;')

                # Replace double spaces by single space.
                while "  " in mwiki:
                    mwiki = mwiki.replace("  ", " ")
                mwiki = mwiki.replace('&lt;!--', '<!--')
                mwiki = mwiki.replace('--&gt;', '-->')

                mwiki = mwiki.replace("'''TOC'''", '__TOC__')
                mwiki = mwiki.replace("'''NOTOC'''", '__NOTOC__')

                revision += mwiki + '</text>\n'
                revision += '</revision>\n'
                revisions.append(revision)
            else:
                if partcount != 1:
                    if not sys.stdout:
                        sys.stdout.write(str(
                            part.get_param('pagename')) + ' version ' + str(
                            part.get_param('version')) + ' wasn\'t counted')

        # Write the contents of `revisions` to the specified output in
        # reverse order to get newest entry last. That maybe unimportant to
        # MediaWiki, but importing the result to XWiki as MediaWiki-Export
        # requires this sorting.
        while revisions:
            revision = str(revisions.pop(-1))
            if revisions:
                revision = revision.replace(
                    '<id>REV_ID_PLACEHOLDER</id>\n',
                    '<id>' + str(len(revisions) + 1) + '</id>\n<parentid>' +
                    str(len(revisions)) + '</parentid>\n')
            else:
                revision = revision.replace(
                    '<id>REV_ID_PLACEHOLDER</id>\n',
                    '<id>' + str(len(revisions) + 1) + '</id>\n')

            mwikixml.write(revision)

        mwikixml.write('</page>\n')
        if uploads:
            filepages[title] = uploads
        pagecount += 1
mwikixml.write('</mediawiki>\n')
sys.stdout.write('\nnumber of pages = ' + str(pagecount)
                 + ' number of versions = ' + str(versioncount) + '\n')
sys.stdout.write('with contributions by ' + str(authors) + '\n')
sys.stdout.write(
    'and file uploads on these pages: ' + str(filepages.keys()) + '\n')
