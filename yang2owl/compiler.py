import sys
import logging

from .yang.lexer import lexer
from .yang.parser import parser
from .yang.structure import check
from .yang.analyzer import analyze

from .owl.factory import OntologyFactory


def __build(input_files, namespace, targets):
    models = []
    logging.debug(f'Compiling {input_files} in format {namespace}')
    logging.debug(f'Ontology {namespace}')
    logging.debug(f'Target modules {targets}')
    logging.info('Start compilation')
    for file in input_files:
        with open(file, 'r', encoding='utf-8') as yang_file:
            try:
                logging.info(f'Parsing {file}')
                lexer.lineno = 0
                model = parser.parse(yang_file.read(), lexer=lexer)
                logging.info(f'Analyzing {file}')
                for e in check(model):
                    logging.error(f'Error compiling {file}: {e}')
                    return 2
                models.append(analyze(model))
            except Exception as e:
                logging.error(f'Error compiling {file}: {e}')
                return 2

    logging.info('Building ontology from input models')
    return OntologyFactory(namespace, models).build(targets)


def convert(yang_modules, namespace, targets):
    models = []
    logging.debug(f'Compiling {yang_modules} to ontology {namespace}')
    logging.debug(f'Target modules {targets}')
    logging.info('Start compilation')

    for file in yang_modules:
        with open(file, 'r', encoding='utf-8') as yang_file:
            try:
                logging.info(f'Parsing {file}')
                lexer.lineno = 0
                model = parser.parse(yang_file.read(), lexer=lexer)
                logging.info(f'Analyzing {file}')
                for e in check(model):
                    logging.error(f'Error in {file}:{e}')
                models.append(analyze(model))
            except Exception as e:
                logging.error(f'Error compiling {file}: {e}')
    logging.info('Building ontology from input models')
    return OntologyFactory(namespace, models).build(targets).ontology
