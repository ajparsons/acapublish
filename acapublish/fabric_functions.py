"""
functions to expand fabric functions - import with *
"""

import shutil
from fabric.api import local
import os

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
 
def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)
    
def scrivner_to_markdown():
    from export import scriv_to_md
    settings = ProjectSettings.settings
    scriv_to_md(settings.SCRIVENER_FOLDER,
                  root=settings.SCRIVENER_ROOT,
                  export_folder = settings.MARKDOWN_FOLDER)    
    print "Exported to markdown"
    
def googlesync():
    
    from google_drive import DriveIntegration
    settings = ProjectSettings.settings
    
    if hasattr(settings,"TEAM_DRIVE"):
        drive = settings.TEAM_DRIVE
    else:
        drive = None
    d = DriveIntegration(drive)
    d.sync_google_doc_folder(settings.MARKDOWN_FOLDER,settings.GOOGLE_DRIVE_PATH)   

def compile(create_pdf=True,create_word=False):
    """
    create pdf from scrivener
    """
    from export import (process_md, create_latex_variables, modify_latex,
                        adjust_mmd_for_word,convert_mmd_to_word,adjust_md_for_latex,scriv_to_md)
    
    settings = ProjectSettings.settings
    
    if hasattr(settings,"SCRIVENER_FOLDER") and settings.SCRIVENER_FOLDER:
        scriv_to_md(settings.SCRIVENER_FOLDER,settings.SCRIVENER_ROOT,settings.MARKDOWN_FOLDER)
    
    process_md(settings.MARKDOWN_FOLDER,
              root=settings.SCRIVENER_ROOT,
              export_file=r"_compile\content.mmd",
              settings = settings
              )

    #import title and author settings
    if create_word:
        adjust_mmd_for_word(r"_compile\content.mmd",
                            r"_compile\content_word.mmd",
                            settings)
        convert_mmd_to_word(r"_compile\content_word.mmd",
                            r"_outputs\master.docx",
                            settings)
    if create_pdf:
        adjust_md_for_latex(r"_compile\content.mmd",
                            r"_compile\content_latex.mmd")
        local(r'multimarkdown -b -t latex _compile\content_latex.mmd')
        modify_latex(r"_compile\content_latex.tex")
        create_latex_variables(settings,r"_compile\article-variables.tex")
        #copy bib file
        if os.path.exists("_images"):
            copytree(r"_images","_compile")
        shutil.copyfile(settings.BIB_FILE,r"_compile\bib.bib")
        local(r'cd _compile && pdflatex master.tex && bibtex master.aux & pdflatex master.tex')
        shutil.copyfile(r"_compile\master.pdf",r"_outputs\master.pdf")