
"""
tools for managing functions that generate tables
"""
from useful_inkleby.files import QuickGrid, QuickText
import os
from tabulate import tabulate
from copy import deepcopy

analysis_folder = r"_analysis"

def if_floatable(func):
    """
    decorator that ensures all input to function are floats
    """
    def inner(x):

        if type(x) == float:
            return func(x)
        try:
            float(x)
            return func(x)
        except ValueError:
            return x

    return inner


class BaseTransformer(object):
    """
    base function adjust the formatting of a column based on it's content
    """

    def get_function(self, col_name, generator):
        return lambda x: x

    def transform(self, qg, col_name):
        function = self.get_function(col_name, qg.get_column(col_name))
        qg.transform(col_name, function)


class CleverNumberTransformer(BaseTransformer):
    """
    depending on properties of whole column, transform into nicer looking numbers
    
    if % - make percentage
    if larger than 1000, comma seperate
    
    """

    def get_function(self, col_name, generator):
        if "%" in col_name:
            return if_floatable(lambda x: "{:0.2f}%".format(float(x)))

        else:
            all = [x for x in generator]
            m = max(all)

            if m > 1000:
                return if_floatable(lambda x: "{:,}".format(int(x)))
            else:
                return if_floatable(lambda x: "{:0.4f}".format(float(x)))


def markdown_table(qg, label, caption):
    """
    generate a markdown table (correctly formatted) of the data
    """

    nqg = QuickGrid(header=list(qg.header))
    nqg.data = deepcopy(qg.data)
    qg = nqg

    class SignifianceManager(object):
        """
        manage how many signifiance levels in this document
        """
        level = 0

        @classmethod
        def notch(cls, x):
            if x > cls.level:
                cls.level = x

        @classmethod
        def significance(cls, x):
            x = float(x)
            s = "{:0.4f}".format(x)
            s = s[1:]

            if x < 0.0001:
                r = "<.0001****"
                cls.notch(4)
            elif x < 0.001:
                r = s + "***"
                cls.notch(3)
            elif x < 0.01:
                r = s + "**"
                cls.notch(2)
            elif x < 0.05:
                r = s + "*"
                cls.notch(1)
            else:
                r = s
            return r

    """
    apply transformation to data
    """

    transform = CleverNumberTransformer()

    for h in qg.header:
        if h.lower() == "p-value":
            qg.transform(h, if_floatable(SignifianceManager.significance))
        else:
            transform.transform(qg, h)

    table = tabulate(
        qg.data, qg.header, tablefmt="pipe", disable_numparse=True)
    nlabel = "table-{0}".format(label.lower())
    if SignifianceManager.level:
        ncaption = caption + "-sigtable{0}".format(SignifianceManager.level)
    else:
        ncaption = caption
    desc = "\n[{0}][{1}]".format(ncaption, nlabel)

    QuickText(text=table + desc).save(os.path.join(analysis_folder,
                                                   "{0}.txt".format(label)))


class AnalysisGroup(object):

    def __init__(self):
        self.key_lookup = {}
        self.func_lookup = {}

    def register_group(self, list_of_analysis):
        """
        register more than one label to a function
        accepts a list of tupes (label, descriptions).
        """
        for l in list_of_analysis:
            self.key_lookup[l[0]] = l[1]

        def inner(func):

            for l in list_of_analysis:
                self.func_lookup[l[0]] = func

            return func

        return inner

    

    def register(self, label, description):
        """
        register function with a label
        """
        self.key_lookup[label] = description

        def inner(func):
            self.func_lookup[label] = func
            func.analysis_label = label
            return func

        return inner

    def save(self, label, qg):
        """
        save csv and markdown
        """
        caption = self.key_lookup[label]
        safe_caption = caption.replace(" ", "_")
        safe_caption = "".join(
            [c for c in safe_caption if c.isalpha() or c.isdigit() or c == '_']).rstrip()
        if os.path.exists(analysis_folder) == False:
            os.makedirs(analysis_folder)
        qg.save(
            [analysis_folder, "{0}_{1}.csv".format(label, safe_caption).lower()])
        markdown_table(qg, label, caption)

    def dispatch(self, label=None):
        """
        run functions depend on label
        """
        
        def save_if_result(func):
            result = func()
            if result:
                self.save(func.analysis_label,result)
                        
        if label == None:
            already_run = []
            for r in self.func_lookup.itervalues():
                if r not in already_run:
                    save_if_result(r)
                    already_run.append(r)
        else:
            save_if_result(self.func_lookup[label])

    def autocomplete(self):
        """
        return ref options to complete scrivener autocomplete
        """
        options = []
        form = "[ref:table-{0}]"
        for k in self.key_lookup.iterkeys():
            options.append(form.format(k.lower()))
        return options