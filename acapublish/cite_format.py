'''
Handles the formatting of citations
'''
#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

from citeproc.source.bibtex import BibTeX
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem
from itertools import izip
from useful_inkleby.files import QuickGrid
from gender_detector import GenderDetector

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
        for i, c in izip(self.items, results):
            yield i, "".join(c)

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

    def __init__(self, bib_file, style="harvard1", formatter=md_cite_formatter, gender_override=None, override_file=None,gender_locale="uk"):
        self.bib_file = BibTeX(bib_file, encoding="utf-8")
        self.bib_style = CitationStylesStyle(style, validate=False)

        self.bibliography = CustomStylesBibliography(self.bib_style,
                                                     self.bib_file,
                                                     formatter)
        self.key_lookup = {}
        self.direct_override = {}
        if override_file:
            qg = QuickGrid().open(override_file)
            self.direct_override = {x["ref"].lower().strip(
            ): x["full"] for x in qg if x["ref"] != None}
        self.gender_qg = QuickGrid(header=[
                                   "key","citation", "author", "first_author", "first_name", "last_name", "year", "gender"])
        self.gd = GenderDetector(gender_locale)
        self.gender_override = gender_override
        self.gender_lookup = None

    def register(self, *keys):
        items = [CitationItem(x) for x in keys]
        cite = Citation(items)
        self.bibliography.register(cite)
        if len(keys) == 1:
            self.key_lookup[keys[0].lower()] = cite
        return cite

    def name(self, object):
        try:
            ref = object.cites[0].reference
        except KeyError:
            return "AUTHOR MISSING", "YEAR MISSING"
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
            name = authors[0]["family"] + ", " + \
                authors[1]["family"] + " and " + authors[2]["family"]
        elif len(authors) > 1:
            name = authors[0]["family"] + " and " + authors[1]["family"]
        elif len(authors) == 1:
            name = authors[0]["family"]
        else:
            name = "AUTHOR MISSING"
        return name, year

    def cite(self, item):

        citation = self.bibliography.cite(item, warn)
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
            citation = citation.replace(year, key_key)

        if ref.key in self.direct_override:
            citation = self.direct_override[ref.key]
        first_author = True
        for a in ref["author"]:
            if "given" in a:
                given = a["given"]
            else:
                given = "MISSING"
            last = a["family"]
            full = given + " " + last
            first = given.split(" ")[0]
            gender = self.gender_guess(first, full)

            self.gender_qg.add(
                [ref.key, citation, full, first_author, first, last, year, gender])
            first_author = False

        return citation

    def gender_guess(self, first, full):
        if self.gender_lookup == None:
            if self.gender_override:
                qg = QuickGrid().open(self.gender_override, force_unicode=True)
                self.gender_lookup = {x[0]: x[1] for x in qg}
            else:
                self.gender_lookup = {}
        if full in self.gender_lookup:
            return self.gender_lookup[full]

        if len(first) == 1:
            return "initial"
        else:
            return self.gd.guess(first)

    def export_gender(self, slug):

        def avg(ll):
            s = sum(ll)
            return s / float(len(ll))

        from collections import Counter

        all = self.gender_qg
        unique_citations = QuickGrid(header=all.header)
        unique_authors = QuickGrid(header=all.header)
        done = []

        previous = None
        skip = False
        for r in self.gender_qg:
            key = r.key
            if r.first_author == True:
                if previous:
                    done.append(previous)
                if key in done:
                    skip = True
                else:
                    skip = False
                    previous = key

            if skip == False:
                unique_citations.add(r)

        done = []
        for r in self.gender_qg:
            key = (r.last_name + r.first_name[0]).lower()
            if key not in done:
                unique_authors.add(r)
                done.append(key)

        all_citations = Counter([x.gender for x in all])
        unique_documents = Counter([x.gender for x in unique_citations])
        first_all_citations = Counter(
            [x.gender for x in all if x.first_author])
        first_unique_documents = Counter(
            [x.gender for x in unique_citations if x.first_author])
        unique_authors = Counter([x.gender for x in unique_authors])

        average_year_men = avg(
            [float(x.year) for x in unique_citations if x.gender == "male" and x.year])
        average_year_female = avg(
            [float(x.year) for x in unique_citations if x.gender == "female" and x.year])
        year_diff = average_year_female - average_year_men

        final = QuickGrid(
            header=["Count", "male", "female", "unknown", "initial", "ratio"])

        all_citations["Count"] = "all authors (all citations)"
        unique_documents["Count"] = "all authors (unique documents)"
        first_all_citations["Count"] = "first authors (all citations)"
        first_unique_documents["Count"] = "first authors (unique documents)"
        unique_authors["Count"] = "unique authors"

        year = {"male": average_year_men,
                "female": average_year_female,
                "Count": "Year Difference",
                "ratio": year_diff}

        final.add(all_citations)
        final.add(unique_documents)
        final.add(first_all_citations)
        final.add(first_unique_documents)
        final.add(unique_authors)

        for r in final:
            total = r.male + r.female
            r.ratio = round((r.female / float(total)) * 100, 2)

        final.add(year)

        self.gender_qg.save(
            ["_outputs", "{0}_gender_authors.csv".format(slug)], force_unicode=True)
        unique_citations.save(
            ["_outputs", "{0}_gender_authors_unique_pub.csv".format(slug)], force_unicode=True)
        final.save(["_outputs", "{0}_gender_results.csv".format(slug)])

    def get_bibliography(self):

        self.bibliography.sort()
        for item, citation in self.bibliography.bibliography():
            ref = item.reference
            year = str(ref["issued"]["year"])

            if item.key[-1] not in string.digits:
                key_key = item.key[-5:]
                citation = citation.replace(year, key_key)

            yield citation
