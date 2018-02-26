"""
functions for creating pdf export from scriviner files

"""
from scrivener_python import Scrivener
from useful_inkleby.files import QuickText
import re
from acapublish.cite_format import CitationProcessor
import os

INSIDE = 1
OUTSIDE = 0
NO_CHANGE = -1
import string
import pypandoc

def construct_sig(level,markdown=False):
    
    if markdown:
        base = ""
        template = "*<SIG"
        asterisk = "\*"
    else:
        base = r"\multicolumn{3}{l}{\rule{0pt}{1.2\normalbaselineskip}% strut" + "\r\n"
        template = r"\textsuperscript{*$p<SIG$"
        asterisk = "\*"
    level_lookup = {1:0.05,
                     2:0.01,
                     3:0.001,
                     4:0.0001}
    
    r = range(1,level+1)[::-1]
    last = r[-1]
    full = base
    for l in r:
        stars = "".join([asterisk for x in range(0,l)])
        line = template
        line = line.replace("*",stars)
        line = line.replace("SIG",str(level_lookup[l]))
        if markdown:
            if l != last:
                line += " "
            else:
                line += "\r\n"           
        else:
            if l != last:
                line += ",} " + "\r\n"
            else:
                line += "}}\r"
        full += line
    
    if markdown:
        full = "_" + full + "_"
    return full


def scriv_to_md(folder,root,export_folder):
        scriv = Scrivener(folder).get(root)
        scriv.write_tree_to_md(export_folder)


def join_markdown(folder):
    
    text = ""
    files = os.listdir(folder)
    files.sort()
    for f in files:
        path = os.path.join(folder,f)
        if os.path.isdir(path):
            text += join_markdown(path) + "\n\r"
        else:
            text += QuickText().open(path).text  + "\n\r"
        
    return text
        

def process_md_old(folder,root,export_file,cite_style="authoryear",ref_sentence=NO_CHANGE):
    """
    convert scrivener file into mmd file
    """
    
    text = join_markdown(folder)     
        
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
                for a in re.finditer("<--\\\\autocite\[.*\]\{([a-zA-Z]*)\d*\}-->",sentence):
                    la = a.group(1).lower()
                    if " " + la + " " in l_sentence or l_sentence[:len(la)] == la:
                        new_sentence = sentence.replace("\\autocite","\\autocite*")
                        text = text.replace(sentence,new_sentence)
                        
                        
        text = text.replace("<--\\","<!--\\").replace("[p--","[p.")
        

    

    
def adjust_mmd_for_word(source_file,export_file,settings):
    
    qt = QuickText().open(source_file)
    
    start_table = None
    replace_queue = []
    table_lookup = {}
    table_count = 0
    for x,l in enumerate(qt.lines()):
        l = l
        if l and l[0] == "|" and start_table == None:
            table_count += 1
            start_table = x
            l.update("<STARTTABLE>!!{0}!!".format(x) + l)
        if start_table and "[table-" in l:
            t = l
            t = t.replace("][","|")
            t = t.replace("[","")
            t = t.replace("]","")
            name, table_id = t.split("|")
            sig = 0
            if "sigtable" in name:
                sig = int(name[-1])
                name = name.replace("-sigtable{0}".format(sig),"")
                sig_level = construct_sig(sig,markdown=True)
                l.update(sig_level + "<ENDTABLE>")
            else:
                l.update("<ENDTABLE>")
            
            new_name = "**Table {0}.** {1}".format(table_count,name)
            
            replace_queue.append(["!!{0}!!".format(start_table),
                                  "{0}\r\n\r\n".format(new_name)])
            table_lookup[table_id.strip()] = table_count
            start_table = None

    
    text = qt.text
    
    for r in replace_queue:
        text = text.replace(*r)

    

    title = "#{0}".format(settings.TITLE)
    
    text = title + "\n\r" + text
    
    tables = []
    count = 1
    if settings.SEPERATE_TABLES:
        for a in re.finditer(r"<STARTTABLE>(.*?)<ENDTABLE>",text, re.DOTALL):
            full = a.group(0)
            ref = a.group(1)
            tables.append(ref)
            text = text.replace(full,"[Insert Table {0}]".format(count))
            count += 1
        table_text = '\n\r<div style="page-break-after: always;"></div>'.join(tables)
        QuickText(text=table_text).save(r"_compile\tables.mmd")
        
            
    
    QuickText(text=text).save(export_file)

    
def adjust_md_for_latex(source_file,export_file):
    
    qt = QuickText().open(source_file)
    text = qt.text
    
    text = text.replace(" .",".")
    text = text.replace("...","$$$ELIPSE%%%")   
    text = text.replace("..",".")   
    text = text.replace("$$$ELIPSE%%%","..."                      )     
        
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
    

def process_md(folder,root,export_file,settings):
    """
    convert scrivener file into mmd file
    """
    
    text = join_markdown(folder)     
    
    qt = QuickText(text=text)
    
    """
    fix tables
    """
    
    start_table = None
    table_lookup = {}
    table_count = 0
    
    for x,l in enumerate(qt.lines()):
        l = l
        if l and l[0] == "|" and start_table == None:
            table_count += 1
            start_table = x
        if start_table and "[table-" in l:
            t = l
            t = t.replace("][","|")
            t = t.replace("[","")
            t = t.replace("]","")
            name, table_id = t.split("|")
        
            table_lookup[table_id.strip()] = table_count
            start_table = None

    text = qt.text

    # replace table references
    
    for a in re.finditer(r"\[ref:(.*?)\]",text):
        full = a.group(0)
        ref = a.group(1)
        table_no = table_lookup[ref]
        text = text.replace(full,"{0}".format(table_no))
    
    #move citations in or out of sentences
    
    if settings.REFS_IN_SENTENCE == INSIDE:
        for r in re.finditer("\.\s*\[#(.*?)\]",text):
            new = u"[#{0}].".format(r.group(1))
            if "*" not in new or "**" in new:
                text = text.replace(r.group(0),new)
    if settings.REFS_IN_SENTENCE == OUTSIDE:
        for r in re.finditer("\[#(.*?)\]\s*\.",text):
            new = u".[#{0}]".format(r.group(1))
            if "*" not in new or "**" in new:
                text = text.replace(r.group(0),new)
    
    
    text = text.replace(" .[#",".[#")
    
    """
    sort out quotations
    
    """
    
    text = quote_processor(text,settings.INITIAL_QUOTES)
    
    """
    do footnotes
    """

    cite = CitationProcessor(settings.BIB_FILE,
                             settings.MARKDOWN_CITE,
                             override_file = settings.OVERRIDE_FILE)
    
    cite_lookup = {}

    if settings.SHORT_CITE:
        references = ["*References:*"]
    else:
        references = []

    for a in re.finditer(r"\[\#(.*?)\]",text):
        
        full = a.group(0)
        doc_ref = a.group(1).split(";")[0]
        if doc_ref[0] == "*":
            doc_ref = doc_ref[1:]
        if doc_ref[0] == "*":
            doc_ref = doc_ref[1:]
        cite_lookup[doc_ref] = cite.register(doc_ref)
        
    cite.bibliography.amend_keys()
        
    for x, a in enumerate(re.finditer(r"\[\#(.*?)\]",text)):
        
        full = a.group(0)
        doc_ref = a.group(1)
        page_reference = ""
        no_name = False
        year_only = False
        
        if ";" in doc_ref:
            doc_ref,page_reference = doc_ref.split(";")
            page_reference = page_reference.strip()

            
        if doc_ref[0] == "*":
            year_only = True
            doc_ref = doc_ref[1:]
            if doc_ref[0] == "*":
                no_name = True
                doc_ref = doc_ref[1:]
            
        if page_reference == None:
            page_reference = ""
        
        cite_object = cite_lookup[doc_ref]
        
        new_ref = cite.cite(cite_object)
        name, year = cite.name(cite_object)
        new_ref = u"".join(new_ref)
        
        if settings.SHORT_CITE:
            
            if no_name:
                short_year_format = " ({1})"
            else:
                short_year_format = "{0} ({1})"
                
            if year_only:
                new_ref = short_year_format.format(name,year)
            
            if page_reference:
                new_ref = new_ref[:-1] + ", " + page_reference + ")" 
            text = text.replace(full,new_ref)
        
        else:
            
            if page_reference:
                new_ref = new_ref[:-1] + ", " + page_reference
            
            ref_format = "[^note{0}]".format(x)
            
            if year_only and no_name == False:
                ref_format =  name + ref_format
            
            new_ref = u"{0}:{1}".format(ref_format,new_ref)
            references.append(new_ref)
            text = text.replace(full,ref_format)
            
    if settings.SHORT_CITE:
        
        for b in cite.get_bibliography():
            references.append(b)
           
    text = text + "\n\r" + "\n\r".join(references)    
    
    text = text.replace(" (","(").replace("("," (")
    
    QuickText(text=text).save(export_file)

        
        

def convert_mmd_to_word(mmd_file,word_file,settings):
    extra_args = ()
    if hasattr(settings,"DOCX_TEMPLATE") and settings.DOCX_TEMPLATE:
        extra_args = ("--reference-docx={0}".format(settings.DOCX_TEMPLATE),)
    
    pypandoc.convert_file(mmd_file,
                          'docx',
                          format="markdown_mmd",
                          outputfile=word_file,
                          extra_args=extra_args)
    print "created {0}".format(word_file)    
    
    if settings.SEPERATE_TABLES:
        table_file = r"_compile\tables.mmd"
        table_word_file = r"_outputs\tables.docx"
        pypandoc.convert_file(table_file,
                              'docx',
                              format="markdown_mmd",
                              outputfile=table_word_file,
                              extra_args=extra_args)
        print "created {0}".format(table_word_file)

    
    
def modify_latex(filename):
    """
    latex file post-processor
    Adds significance indicators to tables.
    
    """

        
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
    
def quote_process_sentence(s,order=1):
    
    if len(s) <= 1:
        return s
    
    def sorter():
        
        yield None,s[0],s[1],0
        for n in range(len(s)-2):
            yield s[n],s[n+1],s[n+2],n+1
        yield s[-2],s[-1],None,len(s)-1
        
    def is_quote_start(p,v,n):
        #none means not quote mark
        #false means end of quote
        #start means beginning of quote
        
        letters = string.ascii_letters + string.digits + '"' + "'"
        letters_no_quotes = string.ascii_letters + string.digits
        if v not in ['"',"'"]:
            return None
        if p == None: #start of line
            return True
        if n == None: #end of line
            return False
        if n in " ." + string.whitespace:
            return False
        if p in " " + '"' + "'":
            return True
        if p in letters_no_quotes and n in letters_no_quotes:
            return None
        if p in letters:
            return False


        
    class QuotePoint(object):
        
        def __init__(self,layer,position,start):
            self.layer = layer
            self.position = position
            self.start = start
            self.potential_override = False
            
        def correct_quote(self):
            if (self.layer - order) % 2 == 0:
                return '"'
            else:
                return "'"
    
    current_layer = 0
    points = []
    start_lookup = {}
    last = None
    for p,c,n,x in sorter():
        quote_start = is_quote_start(p,c,n)
        if points:
            last = points[-1]
        if quote_start == None:
            continue # not a quote mark
        
        if quote_start:
            current_layer += 1
            q = QuotePoint(layer=current_layer,
                           position = x,
                           start=quote_start)
            start_lookup[current_layer] = c
            points.append(q)
        else:
            layer_match = False
            if current_layer:
                opening_character = start_lookup[current_layer]
                if c != opening_character:
                    continue
                else:
                    layer_match = True
            #is the last ending false
            start_count = len([y for y in points if y.start])
            end_count = len([y for y in points if y.start == False]) + 1
            
            if end_count > start_count:
                if last and last.start == False and last.potential_override:
                    points.pop()
                    current_layer += 1
                
            start_count = len([y for y in points if y.start])
            end_count = len([y for y in points if y.start == False]) + 1
            
            if end_count <= start_count:
                q = QuotePoint(layer=current_layer,
                               position = x,
                               start=quote_start)
                if n == " " and layer_match == False:
                    q.potential_override = True
                current_layer -= 1
                points.append(q)
        
    pd = {x.position:x for x in points}
        
    new = []
    new1 = []
    for x,l in enumerate(s):
        if x in pd:
            new.append(pd[x].correct_quote())
            new1.append(pd[x].correct_quote())
        else:
            new.append(l)#
            new1.append(" ")
    #print u"".join(new)
    #print u"".join(new1)
    return u"".join(new)
        
def quote_processor(text,order=2):
    qt = QuickText(text=text)
    qt.text = qt.text.replace(u'\u201c', '"').replace(u'\u201d', '"')
    qt.text = qt.text.replace(u'\u2018', "'").replace(u'\u2019', "'")
    
    
    for l in qt:
        new = quote_process_sentence(l,order)
        l.update(new)
    
    return qt.text
    
if __name__ == "__main__":
    text = QuickText().open(r"E:\sentence_quotes.txt").text
    print quote_processor(text)