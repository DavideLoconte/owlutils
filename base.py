import re

from abc import ABC, abstractmethod
from typing import Dict, Any, Iterable, Union, Optional, List, Set

import owlready2
import owlready2.rply
from owlutils.rule import ExpressionBuilder

AnyOWL = Union[owlready2.AnnotationProperty,
               owlready2.PropertyClass,
               owlready2.Thing,
               owlready2.ThingClass,
               owlready2.Ontology]

class LifecycleSuperclass(ABC):
    """Common superclass for OntologyInterface and OntologyPluginInterface"""
    def pre_update(self) -> None:
        """Invoked before the ontology is updated"""

    def pre_sync(self) -> None:
        """Invoked before the ontology is classified"""

    def pre_save(self) -> None:
        """Invoked before the ontology is saved to a file"""

    def post_update(self) -> None:
        """Invoked after the ontology is updated"""

    def post_sync(self) -> None:
        """Invoked after the ontology is classified"""

    def post_save(self) -> None:
        """Invoked after the ontology is saved to a file"""

class OntologyInterface(LifecycleSuperclass):

    """Wrapper for owlready2 ontologies"""

    # Abstract methods

    def update(self, **kwargs) -> None:
        """Add contextual information to the ontology"""
        self.pre_update()
        self.post_update()

    def map(self, entity_type: str, entity: Dict[str, Any]) -> owlready2.Thing:
        """Map an entity to a individual"""

    # Public methods

    def __init__(self, ontology: owlready2.Ontology):
        self.ontology: owlready2.Ontology = ontology
        self.entities: Dict[owlready2.Thing, Any] = {}
        self.plugins: List[OntologyPluginInterface] = []
        self.imported: Dict[str, Any] = {}

    def sync(self, global_sync: bool = False, debug: int = 0) -> None:
        """Classify the ontology"""
        self.pre_sync()

        if global_sync:
            owlready2.sync_reasoner_pellet(infer_data_property_values=True,
                                           infer_property_values=True,
                                           debug=debug)
        else:
            owlready2.sync_reasoner_pellet(self.ontology,
                                           infer_data_property_values=True,
                                           infer_property_values=True,
                                           debug=debug)

        self.post_sync()

    def get(self, name: str = None) -> Optional[AnyOWL]:
        """Return owlready ontology or an entity"""
        if name is None:
            return self.ontology
        return getattr(self.ontology, name)

    def import_ontology(self, ontology: Any) -> None:
        """Import an ontology"""
        self.imported[ontology.get().name] = ontology
        self.get().imported.append(ontology.get())

    # Lifecycle methods

    def pre_update(self) -> None:
        for plugin in self.plugins:
            plugin.pre_update()

    def pre_sync(self) -> None:
        for plugin in self.plugins:
            plugin.pre_sync()

    def pre_save(self) -> None:
        for plugin in self.plugins:
            plugin.pre_save()

    def post_update(self) -> None:
        for plugin in self.plugins:
            plugin.post_update()

    def post_sync(self) -> None:
        for plugin in self.plugins:
            plugin.post_sync()

    def post_save(self) -> None:
        for plugin in self.plugins:
            plugin.pre_save()

# Ontology plugin interface

class OntologyPluginInterface(LifecycleSuperclass):
    """Abstract class for an ontology plugin"""
    def __init__(self, ontology: OntologyInterface):
        self.ontology = ontology
        self.ontology.plugins.append(self)

    @abstractmethod
    def reserved_names(self) -> Iterable[str]:
        """Names that are reserved to the plugin"""

# Specialized ontology plugin interfaces
class ActuatorInterface(OntologyPluginInterface):
    """
    This abstract class can be extended to create an ontology actuator.
    Ontology actuators associate function to Action individuals in an owl ontology.
    When an axioms states that a Action Acts On a particular individual, the mapped
    python function is invoked passing that individual as an argument
    """
    def __init__(self, ontology: OntologyInterface):

        functions = [func for func in dir(self) if callable(getattr(self, func)) and \
                                                   not func.startswith('_') and \
                                                   func not in dir(ActuatorInterface)]

        with ontology.get():
            class Action(owlready2.Thing):
                """OWL class indicating a generic action"""
                comment = "Added by owlutils"

            class actsOn(Action >> owlready2.Thing):
                """
                OWL Property indicating that a action
                has to be executed on the specific individual
                """
                comment = "Added by owlutils"

            for function in functions:
                Action(function)

        super().__init__(ontology)

    def reserved_names(self) -> Iterable[str]:
        return ["Action", "actsOn"]

    def apply(self, individual: Optional[owlready2.Thing] = None, target: Optional[owlready2.Thing] = None):
        """Execute the inferred actions"""
        response = {"applied-actions": []}
        if individual is None:
            for individual in self.ontology.get().Action.instances():

                for target in individual.actsOn:
                    result = getattr(self, individual.name)(target)
                    response['applied-actions'].append({
                        'action': individual.name,
                        'target': target.name,
                        'result': result
                    })

                name = individual.name
                owlready2.destroy_entity(individual)
                self.ontology.get('Action')(name)

        elif isinstance(individual, self.ontology.get('Action')) and target is None:

            for target in individual.actsOn:
                result = getattr(self, individual.name)(target)
                response['applied-actions'].append({
                    'action': individual.name,
                    'target': target.name,
                    'result': result
                })

            name = individual.name
            owlready2.destroy_entity(individual)
            self.ontology.get('Action')(name)

        elif isinstance(individual, self.ontology.get('Action')) and isinstance(target, owlready2.Thing):
            result = getattr(self, individual.name)(target)
            response['applied-actions'].append({
                'action': individual.name,
                'target': target.name,
                'result': result
            })
            getattr(self.ontology.get(), individual.name).actsOn.remove(target)

        return response


# Concrete plugins

class RuleManager(OntologyPluginInterface):
    """Wrapper to manage SWRL rules with support for class expression"""
    def __init__(self, ontology: OntologyInterface, strict = True):
        super().__init__(ontology)
        self.expression_builder = ExpressionBuilder(ontology.get())
        self.saved_rules: Set[str] = set()
        self.strict = strict

        with ontology.get():
            class Thing(owlready2.Thing):
                """A class to reference owl Things inside rules"""
                equivalent_to = [owlready2.Thing]
                comment = "Added by owlutils"

        for rule in self.rules():
            self.add_rule(rule)

    def rules(self) -> Set[str]:
        """Returns a set of static rules"""
        return set()

    def reserved_names(self) -> Iterable[str]:
        return ["Thing"]

    def pre_sync(self) -> None:
        """Add rules before starting the classification"""

        def print_warning(rule: str, reason: str):
            print(f"Warning, cannot apply rule {rule}")
            print(f"Reason: {reason}")

        with self.ontology.get():
            for rule_expr in self.saved_rules:
                try:
                    rule = owlready2.Imp()
                    rule.set_as_rule(rule_expr)
                except (owlready2.rply.ParsingError, SyntaxError) as err:
                    groups = re.findall(r'\([^()]+\)', rule_expr)
                    expressions = {}

                    for group in groups:
                        if self.expression_builder.is_expression(group[1:-1]):

                            expressions[group] = \
                                    self.expression_builder.expression_to_class(group[1:-1])

                    for expression, class_expression in expressions.items():
                        rule_expr = rule_expr.replace(expression, class_expression.name)

                    try:
                        rule = owlready2.Imp()
                        rule.set_as_rule(rule_expr)
                    except (ValueError, owlready2.rply.ParsingError):
                        print_warning(rule_expr, str(err))

                except (ValueError) as err:
                    print_warning(rule_expr, str(err))

    def post_sync(self) -> None:
        """Remove rules after classification"""
        for rule in self.ontology.get().rules():
            owlready2.destroy_entity(rule)

    def add_rule(self, rule_expr: str):
        """Add a rule to the ontology given its string expression"""
        self.saved_rules.add(rule_expr)

    def remove_rule(self, rule_expr: str):
        """Remove rule from set given"""
        self.saved_rules.remove(rule_expr)

    def replace_rules(self, rules: Iterable[str]):
        """Replace all the rules with the ones passed in the argument"""
        self.saved_rules = set(rules)

    def clear_rules(self):
        """Remove all rules"""
        self.saved_rules = set()
