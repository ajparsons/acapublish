"""
functions for creating pdf export from scriviner files

"""
from scrivener_python import Scrivener
from useful_inkleby.files import QuickText
import re

INSIDE = 1
OUTSIDE = 0
NO_CHANGE = -1

def process_scriv(folder,root,export_file,cite_style="authoryear",ref_sentence=NO_CHANGE):
    """
    convert scrivener file into mmd file
    """
    i = Scrivener(folder).get(root)
    text = i.iter_text()
    
    text = text.replace("\n\n","\n")
    
    final = []
    
    for l in text.split("\n"):
        if "|"  in l:
            final.append(l)
        else:
            final.append(l + "\n")
    
    text = "\n".join(final)
    
    normal = "<!--\\autocite{{0}}-->"
    with_extra = "<!--\\autocite[{1}]{{0}}-->"
    
    #move citations in or out of sentences
    
    if ref_sentence == INSIDE:
        for r in re.finditer("\.\s*\[#(.*?)\]",text):
            new = "[#{0}].".format(r.group(1))
            text = text.replace(r.group(0),new)
    if ref_sentence == OUTSIDE:
        for r in re.finditer("\[#(.*?)\]\s*\.",text):
            new = ".[#{0}]".format(r.group(1))
            text = text.replace(r.group(0),new)
    
    
    #nicely rearrange citation for export
    
    for r in re.findall("\[#(.*?)\]",text):
        
        split = r.split(";")
        if len(split) == 2 and split[1]:
            ref,extra = split
            new = with_extra.replace("{0}",ref).replace("{1}",extra)
        else:
            ref = split[0]
            new = normal.replace("{0}",ref)
        
        total = "[#{0}]".format(r)
        text = text.replace(total,new)
        
        
    #reduces just to year if we're doing that
    
    if "authoryear" in cite_style:
        text = text.replace("<!--\\","<--\\").replace("[p.","[p--")
        for r in re.finditer("\(?[^\.\?\!]+[\.!\?]\)?",text):
            sentence = r.group(0)
            l_sentence = sentence.lower()
            citations = sentence.count("\\autocite")
            if citations == 1:
                
                #if has page details
                for a in re.finditer("<--\\\\autocite\[(.*)]\{(.*)}-->",sentence):
                    la = a.group(2).lower()
                    if " " + la + " " in l_sentence or l_sentence[:len(la)] == la:
                        new_sentence = sentence.replace("\\autocite","\\autocite*")
                        text = text.replace(sentence,new_sentence)                

                #if doesn't have page details - move if possible
                for a in re.finditer("<--\\\\autocite\{([a-zA-Z]*)\d*\}-->",sentence):
                    original = a.group(0)
                    la = a.group(1).lower()
                    etal_rule = "(\w*\sand\s\w*|\w*\,\s\w*\sand\s\w*|\w*\set\sal\.)"
                    for g in re.finditer(etal_rule,sentence):
                        authors = g.group(0)
                        if la in authors.lower():
                            new_sentence = sentence.replace(original,"")
                            original = original.replace("autocite","autocite*")
                            new_sentence = new_sentence.replace(authors,authors+original)
                            text = text.replace(sentence,new_sentence)
                                     
                #if has have page details - shorten if alone
                if "Henderson" in sentence:
                    print "here"
                for a in re.finditer("<--\\\\autocite\[.*\]\{([a-zA-Z]*)\d*\}-->",sentence):
                    la = a.group(1).lower()
                    if " " + la + " " in l_sentence or l_sentence[:len(la)] == la:
                        new_sentence = sentence.replace("\\autocite","\\autocite*")
                        text = text.replace(sentence,new_sentence)
                        
                        
        text = text.replace("<--\\","<!--\\").replace("[p--","[p.")
        
        #remove spaces between end of sentence and footnote
        text = text.replace(". <!--\\",".<!--\\")
        
        #add space between end of word and citation
        for m in re.finditer('([*"\w])<!--\\\\autocite',text):
            all = m.group(0)
            word = m.group(1)
            if word <> ".":
                new = word + " " + all[len(word):]
                text = text.replace(all,new)
            
        
    #nicer intertable link
    new_format = "<!--~\\ref{CITE}-->"
    for r in re.findall("\[ref:(.*?)\]",text):
        total = "[ref:{0}]".format(r)
        new = new_format.replace("CITE",r)
        text = text.replace(total,new)
        
    QuickText(text=text).save(export_file)
    
def create_latex_variables(settings,destination):
    """
    create latex settings file from python settings file
    """
    text = """ 
            \def\mytitle{TITLE}
            \def\myauthor{AUTHOR}
            \usepackage[backend=bibtex,style=CITE]{biblatex}
            """
    text = text.replace("TITLE",settings.TITLE)
    text = text.replace("AUTHOR",settings.AUTHOR)
    text = text.replace("CITE",settings.CITESTYLE)
    QuickText(text=text).save(destination)
    
def modify_latex(filename):
    """
    latex file post-processor
    Adds significance indicators to tables.
    
    """
    def construct_sig(level):
        base = r"\multicolumn{3}{l}{\rule{0pt}{1.2\normalbaselineskip}% strut" + "\r\n"
        template = r"\textsuperscript{*$p<SIG$"
        level_lookup = {1:0.05,
                         2:0.01,
                         3:0.001,
                         4:0.0001}
        
        r = range(1,level+1)[::-1]
        last = r[-1]
        full = base
        for l in r:
            stars = "".join(["*" for x in range(0,l)])
            line = template
            line = line.replace("*",stars)
            line = line.replace("SIG",str(level_lookup[l]))
            if l != last:
                line += ",} " + "\r\n"
            else:
                line += "}}\r"
            full += line
        return full
        
    qt = QuickText().open(filename)
    
    current_sig = None
    for l in qt:
        if r"\caption{" in l and "-sigtable" in l:
            new_text = l.replace("-sigtable","").strip()
            level = int(new_text[-2])
            new_text = new_text[:-2] + "}" + l[-1]
            l.update(new_text)
            current_sig = construct_sig(level)
        if r"\bottomrule" in l and current_sig:
            l.update(l+"\n"+current_sig)
            current_sig = None
    
    qt.save()