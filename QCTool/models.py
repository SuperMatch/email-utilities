#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from django.db import models
from HTMLParser import HTMLParser
from urlparse import urlparse
from htmlentitydefs import entitydefs
import re, codecs


class QCError(models.Model):
    line = models.IntegerField(max_length=10000)
    offset = models.IntegerField(max_length=10000)
    error_message = models.CharField(max_length=50)
    attribute = models.CharField(max_length=20)
    error_code = models.CharField(max_length=500)
    campaign_name = models.CharField(max_length=20)
    campaign_id = models.CharField(max_length=10)
    version = models.IntegerField(max_length=100)


class QCHTMLParser(HTMLParser):
    def __init__(self, data):
        HTMLParser.__init__(self)
        self.originalSource = data
        self.source = data
        self.errMsg = {
            #dictionary for errors. Output method will use the "key" to get the "value" to output the error.
            "invalidImage": "The dimension of the image is invalided.",
            "replaceLink": "Word \"replace\" found in link.",
            "tbd": "Word \"tbd\" found in link.",
            "spaceLink": "Space found before http.",
            "noDotCom": "Can't find .com in the url host.",
            "doubleHttp": "Found http twice in the url.",
            "wrongUrlQuery": "? and & symbol found with wrong order in URL.",
            "wrongFragment": "& or ? symbol found after # symbol, please make sure it's correct.",
            "emptyValue": "Empty value found in ",
            "noAttr": "Unable to find attribute ",
            "returnInAlias": "Found return symbol in alias.",
            "specialChar": "Found special character in the copy.",
            "noHttp": "No http found at the beginning of the url.",
            "wrongConv": "Conversion detected but value invalided.",
            "wrongEntity": "Wrong escaped character found",
            "duplicatedAlias": "Found alias duplicated with former alias",
            "wrongScheme": "Wrong scheme found in the link.",
        }
        #filter is used for some ET links
        self.filter = [
            "%%view_email_url%%",
            "%%ftaf_url%%",
            "%%=GetSocialPublishURL(",
            "%%unsub_center_url%%",
            "%%profile_center_url%%",
            "%%=redirectto("
        ]
        #alias dict is used for counting alias, Key=AliasName Value=Times
        self.aliasDict = {}
        #alias List is used for alias & rawlink pairs
        self.aliasList = []
        #each error will be append to this list
        self.errors = []
        #dict used for counting, notice "plain_link" refers to the aTag which has href
        self.aCount = {
            "view_email": 0,
            "plain_link": 0,
            "empty_link": 0,
            "alias": 0,
            "empty_alias": 0,
            "mail": 0,
            "tel": 0,
            "conversion": 0,
        }
        self.amp = ""
        #cache current line
        self.cur_line = ""
        #signal used for catching title data,
        #I'm still looking into this issue, because if title is null, handle data won't be called
        self.signals = {
            "title": 0, # 0=Unreached, 1=Reached, 2=DataFound
        }
        #below is the special characters used for matching
        mdash = unicode("—", encoding="utf-8")
        lquo = unicode("‘", encoding="utf-8")
        ldquo = unicode("“", encoding="utf-8")
        ellipsis = unicode("…", encoding="utf-8")
        #the characters will be put in to below list
        self.specialCharList = [mdash, lquo, ldquo, ellipsis]

    def run(self):
        self.get_amp()
        code = self.source.split('\n')
        for c in code:
            self.cur_line = c
            for s in c:
                self.feed(s)
            self.feed('\n')

    #decode_html function is used for correct decode our html file
    #if the input is already unicode string, we don't have to use beautiful soup to decode the html
    #If we can easily decode the code to "utf-8", we don't need to use Beautiful Soup also.

    #change the signal
    def changeSignal(self, target, number):
        self.signals[target] = number

    #input error to the list, param "name" used to indicate the specific wrong attr
    def errInput(self, position, errMsg, name=None):
        if errMsg != "over500":
            code = self.cur_line
        else:
            code = "see comments"
        self.errors.append([position[0], position[1], errMsg, name, code])

    #if image don't have either width or height, or both are 0 then it will be reported
    #this may need further discussion, but now it is still working
    def invalidImage(self, width, height):
        if width and height:
            if width == "0" and height == "0":
                self.errInput(self.getpos(), "invalidImage")
        else:
            self.errInput(self.getpos(), "invalidImage")

    #if alias is not found in dict's key, then create one otherwise add 1
    def isAliasDuplicated(self, alias):
        bObj = False
        for item in alias:
            lower_item = item.lower()
            if self.aliasDict.has_key(lower_item):
                self.aliasDict[lower_item] += 1
                bObj = True
            else:
                self.aliasDict[lower_item] = 1
        return bObj

    #the logic is a little confused but it use "urlparse", so check the document
    def urlValidation(self, url):
        if any(url.lower().startswith(x.lower()) for x in self.filter):
            return
        if "replace" in url.lower():
            self.errInput(self.getpos(), "replaceLink")
        elif "TBD" in url.upper():
            self.errInput(self.getpos(), "tbd")
        else:
            purl = urlparse(url)
            if purl.scheme == "" and purl.netloc == "":
                if "http" in purl.path.lower():
                    self.errInput(self.getpos(), "spaceLink")
                elif "tel" in purl.path:
                    pass
                    # UrlMsg += " Tel link;"
                else:
                    self.errInput(self.getpos(), "noHttp")
            elif purl.scheme.lower() == "tel":
                pass
                # UrlMsg += " Tel link;"
            elif purl.scheme.lower() == "mailto":
                pass
                # UrlMsg += " Mail link;"
            elif "http" in purl.scheme.lower():
                if "http" in purl.netloc.lower():
                    self.errInput(self.getpos(), "doubleHttp")
            else:
                self.errInput(self.getpos(), "wrongScheme")

            if purl.query =="":
                if "&" in purl.netloc or "&" in purl.path:
                    self.errInput(self.getpos(), "wrongUrlQuery")
            elif purl.query != "" and ( "&" in purl.path or "?" in purl.query):
                self.errInput(self.getpos(), "wrongUrlQuery")
            if purl.fragment != "" and ( "&" in purl.fragment or "?" in purl.fragment):
                self.errInput(self.getpos(), "wrongFragment")

    #using urlparse to get the scheme of a url
    def getUrlScheme(self, url):
        o = urlparse(url)
        if o.path.startswith("tel:"):
            return "tel"
        return o.scheme

    #check if alias contain return
    def hasReturn(self, alias):
        for item in alias:
            if "\n" in item:
                self.errInput(self.getpos(), "returnInAlias")

    #check if has special char
    def hasSpecialChar(self, content):
        regex = re.compile(r'^[^\x20-\x7E\n\s\r]+$', re.IGNORECASE)
        match = regex.search(content)
        if match:
            self.errInput(self.getpos(), "specialChar")
        else:
            return
        # if any(x in content for x in self.specialCharList):
        #     self.errInput(self.getpos(), "specialChar")

    #only equal true then it will pass the validation
    def convValidation(self, value):
        if value.lower() == "true":
            return True
        return False

    #login the data to alias list
    def aliasInput(self, alias, rawlink, conversion):
        isDuplicated = self.isAliasDuplicated(alias)
        if conversion or conversion == "":
            hasConversion = self.convValidation(conversion)
            if not hasConversion:
                hasConversion = "invalid"
                self.errInput(self.getpos(), "wrongConv")
        else: hasConversion = False
        if not alias:
            aliasStr = "None/Empty"
        else:
            aliasStr = "|".join(alias)
        if not rawlink:
            rawlink = "None/Empty"
        hasConversion = str(hasConversion)
        isDuplicated = str(isDuplicated)
        self.aliasList.append([aliasStr, rawlink, hasConversion, isDuplicated])

    #count the number of the link
    #if we can't get an attr, we will get None
    def count(self, alias, link, conversion):
        scheme = "no href"
        if link is None:
            self.errInput(self.getpos(), "noAttr", "href")
        else:
            scheme = self.getUrlScheme(link)
            self.aCount["plain_link"] += 1
            if link:
                if scheme == "tel":
                    self.aCount["tel"] += 1
                elif scheme == "mailto":
                    self.aCount["mail"] += 1
                elif link == "%%view_email_url%%":
                    self.aCount["view_email"] += 1
            else:
                self.errInput(self.getpos(), "emptyValue", "href")
                self.aCount["empty_link"] += 1
        if len(alias) == 0 and scheme != "tel" and scheme != "mailto":
            self.errInput(self.getpos(), "noAttr", "alias")
        elif len(alias) > 0 and scheme != "tel" and scheme != "mailto":
            self.aCount["alias"] += 1
        elif any(x == "" for x in alias):
            self.aCount["empty_alias"] += 1
            self.errInput(self.getpos(), "emptyValue", "alias")
        if conversion or conversion == "":
            self.aCount["conversion"] += 1

    #while img tag detected, pass it to this method
    def imageCheck(self, attrs):
        width = None
        height = None
        alt = None
        for item in attrs:
            if item[0] == "width":
                width = item[1]
            if item[0] == "height":
                height = item[1]
            if item[0] == "alt":
                alt = item[1]
        self.invalidImage(width, height)
        if alt:
            self.hasSpecialChar(alt)

    #using re to grab the subjectline -- need further test
    # def get_sline(self, text):
    #     regex = re.compile(r'set\s@subjectline\s?=\s?"([^"\\]*(?:\\.[^"\\]*)*)"', re.IGNORECASE)
    #     match = regex.search(text)
    #     if match:
    #         return match.group(1)
    #     else:
    #         return match
    #
    # def get_cid(self, text):
    #     regex = re.compile(r'set\s@subjectline\s?=\s?concat\("([^"\\]*(?:\\.[^"\\]*)*)"', re.IGNORECASE)
    #     match = regex.search(text)
    #     if match:
    #         return match.group(1)
    #     else:
    #         return match
    def get_amp(self):
        amp = re.compile(r'^([\s\S]*?)%%\[([\s\S]*?)\]%%([\s\S]*?)</head>')
        amp_match = amp.search(self.source)
        if amp_match:
            self.amp = amp_match.group(2)
            count = self.amp.count("\n")
            self.source = self.source.replace(self.amp, "\n"*count)
            self.amp = self.amp.replace('\n', '<br />')


    #while a tag detected, pass it to this method
    def aTagCheck(self, attrs):
        link = None
        alias = []
        conversion = None
        for item in attrs:
            if item[0] == "href":
                link = item[1]
            if item[0] == "alias":
                alias.append(item[1])
            if item[0] == "conversion":
                conversion = item[1]
        self.aliasInput(alias, link, conversion)
        self.count(alias, link, conversion)
        #it's quite confusion here, the empty validation is done in count method
        #maybe we can move that out here
        if link:
            self.urlValidation(link)
        if len(alias) != 0:
            self.hasReturn(alias)

    #handle_xxxxx overwrite the blank method in the HTMLParser
    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.imageCheck(attrs)
        elif tag == "a":
            self.aTagCheck(attrs)
        elif tag == "title":
            self.changeSignal("title", 1)

    def handle_endtag(self, tag):
        if tag == "title":
            if self.signals["title"] == 1:
                #if not 2, means not data found. So report error
                self.errInput(self.getpos(), "emptyValue", "title")
            self.changeSignal("title", 0)

    def handle_data(self,data):
        if self.signals["title"] == 1:
            self.changeSignal('title', 2)
        if data:
            self.hasSpecialChar(data)

    #handle_entityref is used for handling escaped character like &amp &reg
    #for now, if we missing semi-colon after the &amp or &reg etc. , we won't catch the missing semi-colon
    #this could be fixed by modify the HTMLParser(Python built-in lib). Won't be difficult.
    def handle_entityref(self, name):
        if not entitydefs.get(name):
            self.errInput(self.getpos(), "wrongEntity")

    #overwrite the original method which will convert the escaped character in the alt attr
    def unescape(self, s):
        return s

    #get result for django
    def getResult(self):
        result = {
            'amp': self.amp,
            'errorList': reversed(self.errors),
            'aliasDict': self.aliasDict,
            'aliasList': self.aliasList,
            'errMsg': self.errMsg,
            'aCount': self.aCount,
        }
        return result

    #output all the errors
    def outputToFile(self, filename):
        filename = self.cid + filename
        outFile = codecs.open(filename, "w", "utf-8")
        #output the sline
        outFile.write("\n"*2 + "The subjectline in AMPScript is:\n")
        outFile.write("*"*50 + "\n"*2)
        outFile.write(self.sline + "\n"*2)
        outFile.write("*"*50 + "\n"*2)
        #output the error pool
        outFile.write("\n"*2 + "*"*50 + "\n"*2)
        outFile.write("Outputting Errors......\n\n")
        outFile.write("*"*50 + "\n"*2)
        for error in reversed(self.errors):
            if not error[-1]:
                error[-1] = ""
            outputStr = "Line: " + str(error[0]) + " Offset: " + str(error[1]) + " Error Message: " + self.errMsg[error[2]] + error[3] + "\n"
            outFile.write(outputStr)
        # output the alias counting problems
        outputStr = ""
        duplicatedones = []
        for key in self.aliasDict:
            outputStr += str(key) + "\t" + str(self.aliasDict[key]) + "\n"
            if self.aliasDict[key] >1:
                duplicatedones.append(str(key))
        outFile.write("\n"*2 + "*"*50 + "\n"*2)
        outFile.write("Outputting Alias Duplicated times, if number equals 1, then means it's not duplicated.\n\n")
        outFile.write("*"*50 + "\n"*2)
        outFile.write("Following alias are duplicated. \n" + "\n".join(duplicatedones) + "\n"*2)
        outFile.write("Alias Name\tAppear times\n")
        outFile.write(outputStr + "\n")
        # output the count pool
        outFile.write("\n"*2 + "*"*50 + "\n"*2)
        outFile.write("Outputting the counts of the a tags\n\n")
        outFile.write("*"*50 + "\n"*2)
        for key in self.aCount:
            outFile.write(str(key) + " : " + str(self.aCount[key]) + "\n")
        # output the alias rawlink pairs
        outFile.write("\n"*2 + "*"*50 + "\n"*2)
        outFile.write("Outputting Alias , Rawlinks combination...\n\n")
        outFile.write("*"*50 + "\n"*2)
        outFile.write("Alias Name\tRaw Links\tConversion\tisDuplicated\n\n")
        for alias in self.aliasList:
            outputStr = "\t".join(alias) + "\n"
            outFile.write(outputStr)
        outFile.close()