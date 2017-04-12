"""
functions for working with bibtex files and syncing with other processes
"""

import bibtexparser
from scrivener_python import Scrivener

def get_ids_from_bibtex(filename):
    """
    return the citation ref for all in database
    """
    with open(filename) as bibtex_file:
        bibtex_str = bibtex_file.read()
        
    bib_database = bibtexparser.loads(bibtex_str)
    
    return [x["ID"] for x in bib_database.entries]

def update_autocomplete(scrivener_project,
                        bibtex_file,
                        extras=[]):
    """
    amends scrivener file with new autocomplete based on bibtex
    """
    transform = lambda x: u"[#{0};]".format(x)
    
    s = Scrivener(scrivener_project)
    existing = set(s.get_autocomplete())
    bib = set([transform(x) for x in get_ids_from_bibtex(bibtex_file)] + extras)
    new = list(bib.difference(existing))
    for n in new:
        s.add_autocomplete(n)
    print "added {0} references".format(len(new))
    s.save()
    

