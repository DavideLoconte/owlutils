"""Create classes equivalent to class expression in order to be parsed into owlready2"""
import types
from urllib.parse import urlparse
from typing import List

import owlready2
from owlutils.lexer import rule_lexer as lexer


class ExpressionBuilder:
    """Class responsible for the creation of class from class expressions"""
    def __init__(self, ontology):
        self.ontology: owlready2.Ontology = ontology
        self.__all_ontologies: List[owlready2.Ontology] = [self.ontology]
        self.__all_ontologies.extend(x for x in self.ontology.imported_ontologies)

    @staticmethod
    def is_iri(expression: str) -> bool:
        """Return true if the string is an iri"""
        iri = urlparse(expression)

        return iri.scheme.lower() in ["http", "https"] and \
               len(iri.netloc) != 0 and \
               len(iri.fragment) != 0

    @staticmethod
    def iri_of(owl_class_name: str) -> str:
        """Return the iri of the input class name"""
        if not ExpressionBuilder.is_iri(owl_class_name):
            raise SyntaxError(f"{owl_class_name} Not a Valid IRI")

        iri = urlparse(owl_class_name)

        return f"{iri.scheme}://{iri.netloc}{iri.path}#"

    @staticmethod
    def class_name(iri: str):
        """Return the fragment of the input iri"""
        if ExpressionBuilder.is_iri(iri):
            return urlparse(iri).fragment
        else:
            return iri

    def class_from_iri(self, cls: str) -> owlready2.ThingClass:
        """Return the class starting from the class"""
        if self.is_iri(cls):
            iri = ExpressionBuilder.iri_of(cls)
        else:
            iri = self.ontology.base_iri

        cls = self.class_name(cls)
        ontology = self.ontology_from_iri(iri)

        if ontology.base_iri == iri and getattr(ontology, cls):
            return getattr(ontology, cls)

        raise NameError(f"Cannot find class {cls} in intento.py {ontology.name}")

    def ontology_from_iri(self, iri: str) -> owlready2.Ontology:
        """Return the ontology associated with input iri"""
        for ontology in self.__all_ontologies:
            if ontology.base_iri == iri:
                return ontology

        raise NameError(f"Cannot find ontology {iri}")

    def expression_to_class(self, expression: str) -> owlready2.ThingClass:
        """Create a class starting from an expression"""
        lexer.input(expression)
        expression_domain = lexer.token()
        expression_restriction = lexer.token()
        expression_range = lexer.token()
        domain_class = self.class_from_iri(expression_domain.value)

        class_expression = "".join([
            str(expression_domain.value).split('#')[-1],
            str(expression_restriction.type).split('#')[-1],
            str(expression_restriction.value).split('#')[-1],
        ])

        if domain_class is None:
            raise SyntaxError(expression_domain.value + " not found in expr " + expression)

        if expression_range is not None:
            class_expression += "-" + expression_range.value.split('#')[-1]
            range_class = self.class_from_iri(expression_range.value)
            if range_class is None:
                raise SyntaxError(expression_domain.value + " not found in expr " + expression)
        else:
            range_class = owlready2.Thing

        restriction_type = expression_restriction.type.lower()

        with self.ontology:
            new_class = types.new_class(class_name(class_expression), (owlready2.Thing,))
            if isinstance(domain_class, owlready2.ObjectPropertyClass):

                if restriction_type == 'min':
                    new_class.is_a.append(
                        domain_class.min(int(expression_restriction.value), range_class))

                if restriction_type == 'exactly':
                    new_class.is_a.append(
                        domain_class.exactly(int(expression_restriction.value), range_class))

                if restriction_type == 'max':
                    new_class.is_a.append(
                        domain_class.max(int(expression_restriction.value), range_class))

                if restriction_type == 'some':
                    new_class.is_a.append(
                        domain_class.some(range_class))

                if restriction_type == 'only':
                    new_class.is_a.append(
                        domain_class.only(range_class))

            elif isinstance(domain_class, owlready2.DataPropertyClass):

                if restriction_type == 'min':
                    new_class.is_a.append(domain_class.min(int(expression_restriction.value)))

                if restriction_type == 'exactly':
                    new_class.is_a.append(domain_class.exactly(int(expression_restriction.value)))

                if restriction_type == 'max':
                    new_class.is_a.append(domain_class.max(int(expression_restriction.value)))

            return new_class

    def is_expression(self, expression: str) -> bool:
        """Return true if string is a supported class expression"""
        try:
            lexer.input(expression)
            expression_domain = lexer.token()
            expression_restriction = lexer.token()
            expression_range = lexer.token()
            legal_restrictions = ["SOME", "ONLY", "MIN", "MAX", "EXACTLY"]

            return (expression_domain.type == "ID") and \
                   (expression_restriction.type in legal_restrictions) and \
                   (expression_range is None or expression_range.type == "ID")

        except AttributeError:
            return False

def class_name(name: str):
    """Normalize string to match the class naming convention"""
    string = individual_name(name)
    return string[0].upper() + string[1:]


def individual_name(name: str) -> str:
    """Normalize a string to match the individual naming convention"""
    name: str = normalize(name)

    if len(name.strip()) == 0:
        return ''

    char_list: List[str] = list(name)
    return ''.join(char_list)


def normalize(value: str) -> str:
    """Normalize a string by removing '-' and capitalizing the following character"""
    char_list: List[str] = list(value)
    length: int = len(char_list)

    for i in range(1, length):
        if char_list[i - 1] in ['-']:
            char_list[i] = char_list[i].upper()

    return ''.join(char_list).replace('-', '')


def role_name(subject: str, predicate: str, obj: str):
    """Create a role name from input strings matching the property naming convention"""
    string = normalize(f'{subject}-{predicate}-{obj}')
    return string[0].lower() + string[1:]
