from typing import List, Set
from ply.lex import lex, LexToken

keywords: Set[str] = {
    'anyxml',
    'argument',
    'augment',
    'base',
    'belongs-to',
    'bit',
    'case',
    'choice',
    'config',
    'contact',
    'container',
    'default',
    'description',
    'enum',
    'error-app-tag',
    'error-message',
    'extension',
    'deviation',
    'deviate',
    'feature',
    'fraction-digits',
    'grouping',
    'identity',
    'if-feature',
    'import',
    'include',
    'input',
    'key',
    'leaf',
    'leaf-list',
    'length',
    'list',
    'mandatory',
    'max-elements',
    'min-elements',
    'module',
    'must',
    'namespace',
    'notification',
    'ordered-by',
    'organization',
    'output',
    'path',
    'pattern',
    'position',
    'prefix',
    'presence',
    'range',
    'reference',
    'refine',
    'require-instance',
    'revision',
    'revision-date',
    'rpc',
    'status',
    'submodule',
    'type',
    'typedef',
    'unique',
    'units',
    'uses',
    'value',
    'when',
    'yang_modules-version',
    'yin-element'
}

tokens: List[str] = [
    'STRING',
    'KEYWORD',
    'CONCAT'
 ]

literals: List[str] = [';', '{', '}']

t_ignore = '\t\r '


def t_COMMENT(t: LexToken) -> None:
    r"""(/\*([^*]|[\r\n\s]|(\*+([^*/]|[\r\n\s])))*\*+/)|(//.*)|(/\*.*)"""
    nlines = 0
    for chr in t.value:
        if chr == '\n':
            nlines += 1
    t.lexer.lineno += nlines


def t_SQUOTED_STRING(t: LexToken) -> LexToken:
    r"""\'([^\'])*\'"""
    t.type = 'STRING'
    t.value = t.value[1:-1]
    for chr in t.value:
        if chr == '\n':
            t.lexer.lineno += 1
    return t


def t_DQUOTED_STRING(t: LexToken) -> LexToken:
    r"""\"((\\{2})*|((.|\n|\r|\t)*?[^\\](\\{2})*))\""""
    for chr in t.value:
        if chr == '\n':
            t.lexer.lineno += 1
    t.value = t.value[1:-1]
    t.type = 'STRING'
    return t


def t_CONCAT(t: LexToken) -> LexToken:
    r"""\+"""
    return t


def t_KEYWORD(t: LexToken) -> LexToken:
    r"""([^\{\}\;\ \t\n\r])+"""
    return t


def t_ignore_NEWLINE(t: LexToken) -> None:
    r"""\n+"""
    t.lexer.lineno += len(t.value)


def t_error(t: LexToken) -> None:
    raise ValueError(f"Illegal {t.type} \"{t.value}\" at {lexer.lineno + 1}")


lexer = lex()
