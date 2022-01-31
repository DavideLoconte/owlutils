from .tree import Root, Node, Leaf
from .lexer import *
import ply.yacc
import logging

errors: List[str] = []
start: str = 'root_stmt'
__l_brackets: int = 0
__r_brackets: int = 0


def p_lbracket(p):
    """
        lbracket : '{'
    """
    global __l_brackets
    __l_brackets += 1
    p[0] = p.lineno(1)


def p_rbracket(p):
    """
        rbracket : '}'
    """
    global __r_brackets
    __r_brackets += 1
    p[0] = p.lineno(1)


def p_unclosed_stmt(_):
    """
        stmt : key value lbracket stmts
    """
    print('Error, missing } ')
    raise SyntaxError


# Start statement must have a body
def p_root_stmt(p):
    """
        root_stmt : key value lbracket stmts rbracket
    """
    p[0] = Root(
        key=p[1],
        value=p[2],
        children=p[4],
        start=p[3],
        end=p[5],
    )
    logging.debug(f'Module statement: ({p[0].key}, {p[0].value} at lines {p[0].start} ÷ {p[0].end})')


def p_empty_value(p):
    """
        empty :
    """
    p[0] = ''


def p_keyword(p):
    """
        key : KEYWORD
            | string
    """
    p[0] = p[1]


def p_identifier(p):
    """
        value : KEYWORD
              | string
              | empty
    """
    p[0] = p[1]


def p_string_cat(p):
    """
        string : STRING CONCAT string
    """
    p[0] = p[1] + p[3]


def p_string_cat_direct(p):
    """
        string : STRING string
    """
    p[0] = p[1] + p[2]


def p_string(p):
    """
        string : STRING
    """
    p[0] = p[1]


def p_parent_stmt(p):
    """
        stmt : key value lbracket stmts rbracket
             | key value lbracket stmts rbracket ';'
    """
    p[0] = Node(
        key=p[1],
        value=p[2],
        children=p[4],
        start=p[3],
        end=p[5]
    )
    logging.debug(f'Node statement: ({p[0].key}, {p[0].value} at lines {p[0].start} ÷ {p[0].end})')


def p_parent_stmt_no_children(p):
    """
        stmt : key value lbracket empty rbracket
             | key value lbracket empty rbracket ';'
    """
    p[0] = Node(
        key=p[1],
        value=p[2],
        children=[],
        start=p[3],
        end=p[5]
    )
    logging.debug(f'Node statement: ({p[0].key}, {p[0].value} at lines {p[0].start} ÷ {p[0].end})')


def p_leaf_stmt(p):
    """
        stmt : key value ';'
    """
    p[0] = Leaf(
        key=p[1],
        value=p[2],
        start=p.lineno(3) + 1
    )
    logging.debug(f'Leaf statement: ({p[0].key}, {p[0].value} at lines {p[0].start} ÷ {p[0].end})')


def p_stmts(p):
    """
        stmts : stmt stmts
    """
    p[2].append(p[1])
    p[0] = p[2]


def p_stmts_end(p):
    """
        stmts : stmt
    """
    p[0] = [p[1]]


# Error Handling
def p_error(p):

    logging.debug('Parsing error detected')

    if p is None:
        raise ValueError(f'Unterminated statement detected. Check for unbalanced brackets')
    else:
        if p.type.lower() == p.value:
            raise ValueError(
                f'Unexpected {p.type.lower()}, check for missing bracket or semicolon at line {p.lineno}'
            )
        else:
            raise ValueError(
                f'Unexpected {p.type.lower()} "{p.value}", check for missing bracket or semicolon at line {p.lineno}'
            )


parser = ply.yacc.yacc()
