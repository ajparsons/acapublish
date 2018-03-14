'''
Created on 11 Jul 2017

@author: Alex
'''
#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

# The references are parsed from a BibTeX database, so we import the
# corresponding parser.
from citeproc.source.bibtex import BibTeX
# Import the citeproc-py classes we'll use below.
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem
from itertools import izip
from useful_inkleby.files import QuickGrid
import re
try:
    from . import md_cite_formatter
except:
    import md_cite_formatter
import string


def warn(citation_item):
    try:
        print("WARNING: Reference with key '{}' not found in the bibliography."
              .format(citation_item.key))
    except UnicodeEncodeError:
        print ("Unicode error on ref error")
        


class CustomStylesBibliography(CitationStylesBibliography):
    pass

    def bibliography(self):
        results = self.style.render_bibliography(self.items)
        for i,c in izip(self.items,results):
            yield i,"".join(c)
            
    def amend_keys(self):
        return None
        # doesn't work
        for i in self.items:
            ref = i.reference
            key = ref["key"]
            year = str(ref["issued"]["year"])
            if key[-1] not in string.digits:
                ref["issued"]["year"] = key[-5:]
                    


class CitationProcessor(object):
    
    def __init__(self,bib_file,style="harvard1",formatter=md_cite_formatter,override_file=None):
        self.bib_file = BibTeX(bib_file,encoding="utf-8")
        self.bib_style = CitationStylesStyle(style, validate=False)

        self.bibliography = CustomStylesBibliography(self.bib_style,
                                                       self.bib_file,
                                                       formatter)
        self.key_lookup = {}
        self.direct_override = {}
        if override_file:
            qg = QuickGrid().open(override_file)
            self.direct_override = {x["ref"].lower().strip():x["full"] for x in qg if x["ref"] != None}

    def register(self,*keys):
        items = [CitationItem(x) for x in keys]
        cite  = Citation(items) 
        self.bibliography.register(cite)
        if len(keys) == 1:
            self.key_lookup[keys[0].lower()] = cite
        return cite
    
    def name(self,object):
        try:
            ref = object.cites[0].reference
        except KeyError:
            return "AUTHOR MISSING","YEAR MISSING"
        if "author" in ref:
            authors = ref["author"]
        else:
            authors = []
        key = ref["key"]
        year = ""
        if "issued" in ref:
            issued = ref["issued"]
            if "year" in issued:
                year = str(issued["year"])
        
        if year and key[-1] not in string.digits:
            year = key[-5:]
        
        if len(authors) > 3:
            name = authors[0]["family"] + " et al."
        elif len(authors) == 3:
            name = authors[0]["family"] + ", " + authors[1]["family"] + " and " + authors[2]["family"]
        elif len(authors) > 1:
            name = authors[0]["family"] + " and " + authors[1]["family"]
        elif len(authors) == 1:
            name = authors[0]["family"]
        else:
            name = "AUTHOR MISSING"
            
        return name, year
        
    def cite(self,item):
        

        
        citation = self.bibliography.cite(item,warn)
        citem = item.cites[0] 
        try:
            ref = citem.reference
        except KeyError:
            try:
                print (u"missing: {0}".format(citem.key))
            except UnicodeEncodeError:
                print ("missing but unicode error")
            return "MISSING CITATION"
        
        year = None
        if "issued" in ref:
            issued = ref["issued"]
            if "year" in issued:
                year = str(issued["year"])
        
        if year and ref.key[-1] not in string.digits:
            key_key = ref.key[-5:]
            citation = citation.replace(year,key_key)
            
        if ref.key in self.direct_override:
            citation = self.direct_override[ref.key]
            
        return citation
    
    def get_bibliography(self):
        
        self.bibliography.sort()
        for item, citation in self.bibliography.bibliography():
            ref = item.reference
            year = str(ref["issued"]["year"])
            
            if item.key[-1] not in string.digits:
                key_key = item.key[-5:]
                citation = citation.replace(year,key_key)
            
            yield citation


if __name__ == "__main__":
    
    c = CitationProcessor("E:\\Users\\Alex\\Dropbox\\bibtex\\Suicide.bib", style="modern-humanities-research-association")
    
    o = c.register("Pirkis2001b")
    
    print (c.cite(o))
    for b in c.get_bibliography():
        print (b)