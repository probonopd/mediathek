#!/usr/bin/python
# -*- coding: utf-8 -*-

xml_file_path = "/tmp/mediathek_xml"
max_age = 6000

from StringIO import StringIO
from elementtree.ElementTree import ElementTree  # easy_install ElementTree works on Cloud9 :-)
import md5, os, sys, tempfile, time, urllib, bz2, re

class DiskCacheFetcher:
    """Based on http://developer.yahoo.com/python/python-caching.html"""
    def __init__(self, cache_dir=None):
        # If no cache directory specified, use system temp directory
        if cache_dir is None:
            cache_dir = tempfile.gettempdir()
        self.cache_dir = cache_dir
        self.filepath=""
    def fetch(self, url, max_age=max_age):
        # Use MD5 hash of the URL as the filename
        filename = md5.new(url).hexdigest()
        filepath = os.path.join(self.cache_dir, filename)
        if (not (os.path.exists(filepath)) or (not int(time.time()) - os.path.getmtime(filepath) < max_age)) :
            print "Downloading file..."
            # Retrieve over HTTP and cache, using rename to avoid collisions
            data = urllib.urlopen(url).read()
            fd, temppath = tempfile.mkstemp()
            fp = os.fdopen(fd, 'w')
            fp.write(data)
            fp.close()
            os.rename(temppath, filepath)
        self.filepath = filepath

class Fetcher(object):
    def get_latest_bz2(self):
        print "Refreshing cache..."
        F = DiskCacheFetcher()
        url = "http://zdfmediathk.sourceforge.net/update.xml"
        F.fetch(url) # takes a really long time here
        # print F.filepath
        doc = ElementTree(file=F.filepath)
        servers = []
        for e in doc.findall('Server/Download_Filme_1'): #####
            servers.append(e.text)
        dates = []
        for e in doc.findall('Server/Datum'): #####
            dates.append(e.text)
        assert(len(servers) == len(dates))
        pairs = sorted(zip(servers, dates), key=lambda pair: pair[1])
        last_url = pairs[len(pairs)-1][0]
        F.fetch(last_url)
        print F.filepath
        f = open(xml_file_path, 'w')
        f.write(bz2.BZ2File(F.filepath).read()) # takes 3 seconds here
        f.close()
        return True

class Extractor:
    def extract(__self__, line, tag):
        pattern = "<"+ tag + ">(.*?)</" + tag + ">"
        result = re.findall(pattern, line, flags=0)
        if len(result)>0:
            return result[0]
        else:
            return None

def main(search_query="Wetter"):
    fe = Fetcher()
    if (not (os.path.exists(xml_file_path)) or (not int(time.time()) - os.path.getmtime(xml_file_path) < max_age)) :
        bz2 = fe.get_latest_bz2()
    print("starting to parse")
    e = Extractor()
    for line in open(xml_file_path):
        if search_query in line:
            # print line
            url = e.extract(line, "g")
            filenameorig = url.split("/")[-1]
            suffix = url.split(".")[-1]
            outfile = ("_".join(re.findall(r"[A-Za-z0-9üäöÜÄÖß.]*", e.extract(line, "d"))).replace("__","_").replace("__","_") + filenameorig)
            if(e.extract(line, "i") == None):
                command = ( "flvstreamer -r '%s' -e -o '%s'" % (url, outfile))
            else:
                command = ( "flvstreamer %s -e -o '%s'" % (e.extract(line, "i"), outfile))
            for x in ("d", "e", "f"):
            # for x in ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"):
                print("%s: %s") % (x, e.extract(line, x))
            print("%s") % (command)
            print "\n===================\n"
            

"""
<a>Nr</a>
<b>Sender</b>
<c>Thema</c>
<d>Titel</d>
<e>Datum</e>
<f>Zeit</f>
<g>Url</g>
<h>UrlOrg</h>
<i>UrlRTMP</i>
<j>UrlAuth</j>
<k>UrlThema</k>
<l>Abo-Name</l>
"""

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: %s 'query string'" % (sys.argv[0]))