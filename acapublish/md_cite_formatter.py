'''
Created on 11 Jul 2017

@author: Alex
'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


def preformat(text):
    return text


class TagWrapper(str):
    tag = None
    attributes = None

    @classmethod
    def _wrap(cls, text):
        return '{tag}{text}{tag}'.format(tag=cls.tag, text=text)

    def __new__(cls, text):
        return super(TagWrapper, cls).__new__(cls, cls._wrap(text))


class Italic(TagWrapper):
    tag = '*'


class Oblique(Italic):
    pass


class Bold(TagWrapper):
    tag = '__'


class Light(TagWrapper):
    tag = 'l'


class Underline(TagWrapper):
    pass


class Superscript(TagWrapper):
    tag = '^'


class Subscript(TagWrapper):
    tag = '~'


class SmallCaps(TagWrapper):
    pass
