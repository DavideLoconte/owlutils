
#pylint: disable=invalid-name
"""Lexer for atomic class expressions"""
import re
from typing import List

from ply.lex import lex


tokens: List[str] = [
    'MIN',
    'MAX',
    'EXACTLY',
    'SOME',
    'ONLY',
    'VARIABLE',
    'ID'
]

t_ignore = ' \t'

def t_MIN(t):
    r"""min[\ \t \n]+[0-9]+"""
    t.value = int(re.sub('[^0-9]', '', t.value))
    return t


def t_MAX(t):
    r"""max[\ \t \n]+[0-9]+"""
    t.value = int(re.sub('[^0-9]', '', t.value))
    return t


def t_EXACTLY(t):
    r"""exactly[\ \t \n]+[0-9]+"""
    t.value = int(re.sub('[^0-9]', '', t.value))
    return t


def t_SOME(t):
    r"""some"""
    return t


def t_ONLY(t):
    r"""only"""
    return t


def t_VARIABLE(t):
    r'[\?][^\(\)\ ]+'
    return t


def t_ID(t):
    r'[^\?][^\(\)\ ]+'
    return t


def t_error(t):
    """Error callback function"""
    raise SyntaxError(f"Illegal character {t.value[0]} in token {t.value}")


rule_lexer = lex()
