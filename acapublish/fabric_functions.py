"""
functions to expand fabric functions - import with *
"""

import shutil
from fabric.api import local

class ProjectSettings(object):
    settings = None
    analysis_group = None

def set_settings(new):
    ProjectSettings.settings = new
    
def set_analysis_group(new):
    ProjectSettings.analysis_group = new

def analysis(label=None):
    """
    given a label generates excel and markdown file for table.
    If no label, generates all.
    """
    ProjectSettings.analysis_group.dispatch(label)

def updatebib():
    """
    updates the autocomplete from the bibfile
    """
    from bibsync import update_autocomplete
    ag = ProjectSettings.analysis_group
    settings = ProjectSettings.settings
    if ag:
        autocomplete = ag.autocomplete()
    else:
        autocomplete = None
        
    update_autocomplete(settings.SCRIVENER_FOLDER,
                        settings.BIB_FILE,
                        autocomplete)
    
def compile(create_pdf=True):
    """
    create pdf from scrivener
    """
    from export import process_scriv, create_latex_variables, modify_latex
    settings = ProjectSettings.settings
    process_scriv(settings.SCRIVENER_FOLDER,
                  root=settings.SCRIVENER_ROOT,
                  export_file=r"_compile\content.mmd",
                  cite_style = settings.CITESTYLE,
                  ref_sentence=settings.REFS_IN_SENTENCE
                  )
    local(r'multimarkdown -b -t latex _compile\content.mmd')
    modify_latex(r"_compile\content.tex")
    #import title and author settings
    if create_pdf == True:
        create_latex_variables(settings,r"_compile\article-variables.tex")
        #copy bib file
        shutil.copyfile(settings.BIB_FILE,r"_compile\bib.bib")
        local(r'cd _compile && pdflatex master.tex && bibtex master.aux & pdflatex master.tex')
        shutil.copyfile(r"_compile\master.pdf",r"_outputs\master.pdf")