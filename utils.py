"""A OWL Interface abs class for ontologies generated starting from YANG modules"""

import json
from typing import Union, Dict, Any, Optional, Set, List, Tuple

import owlready2 as owl
from owlutils.base import OntologyInterface
from yang2owl.owl.naming import class_name, role_name

Value = Union[int, float, str, bool]
ThingRef = str
Thing = Union[owl.Thing, ThingRef]

def convert_value(value: Value) -> Value:
    """Converts value to the correct data type"""
    try:
        if float(int(value)) == float(value):
            return int(value)
        return float(value)
    except ValueError:
        try:
            if value.lower().strip() in ['true', 'false']:
                return bool(value)
        except ValueError:
            pass
    return str(value)

class YANGOntology(OntologyInterface):
    """Abstract class for ontologies generated with yang2OWL"""

    def get_name(self, key: str, value: Dict[str, Value]):
        """Override this so that it returns a unique name for the entity"""
        raise NotImplementedError

    # Impl

    def __init__(self, ontology: owl.Ontology):
        super().__init__(ontology)
        self.__role_cache: Dict[Tuple[owl.ThingClass, owl.ThingClass], str] =  {}

    def map(self, entity_type: str, entity: Dict[str, Any]) -> owl.Thing:
        return self._entity_to_individual(entity_type, entity)

    def update(self, **kwargs) -> None:
        super().update(**kwargs)
        owl.AllDifferent([x for x in self.ontology.individuals()])

    def _exists(self, element: str) -> bool:
        """Return true if ontology contains a name"""
        return self.get(element) is not None

    def _entity_to_individual(self,
                              entity_type: str,
                              descriptor: Dict[str, Any]) -> Optional[owl.Thing]:

        """Recursively generate a owl individual starting from the descriptor"""
        individual_class: Optional[owl.Thing] = self.get(class_name(entity_type))

        if individual_class is None:
            return None

        name = self.get_name(entity_type, descriptor)
        individual = individual_class(name)
        self._parse_descriptor(individual, descriptor)
        return individual

    def _parse_descriptor(self,
                          individual: owl.Thing,
                          descriptor: Dict[str, Any]) -> None:
        """
        Generate and appends child individuals
        and sub-properties starting from individual descriptor
        """

        ignored: Dict[str, Any] = {}

        for key, val in descriptor.items():
            prop_name: Optional[str] = self._get_role_name(type(individual), key)

            if role_name is None:
                ignored[key] = val
                continue

            prop: owl.PropertyClass = self.get(prop_name)

            if isinstance(prop, owl.DataPropertyClass):
                ignored[key] = self._parse_data_property(individual, prop, val)
            elif isinstance(prop, owl.ObjectPropertyClass):
                ignored[key] = self._parse_object_property(individual, prop, key, val)
            else:
                ignored[key] = val

        individual.comment = json.dumps({k: v for k, v in ignored.items() if v is not None and v != []})

        for atom in list(individual.is_a):
            if isinstance(atom, owl.Restriction) and atom.type == 26:
                atom.cardinality = len(getattr(individual, atom.property.name))


    def _get_role_name(self, owl_subject: owl.ThingClass,
                             owl_object: str) -> Optional[str]:
        """Return the property name between two classes or their nearest ancestors"""

        name: str = role_name(owl_subject.name, "has", owl_object)

        if self.get(name) is not None:
            return name

        cache_entry = self.__role_cache.get((owl_subject, owl_object), None)

        if cache_entry is not None and self.get(cache_entry) is not None:
            return cache_entry
        elif cache_entry is not None:
            del self.__role_cache[(owl_subject, owl_object)]

        o_class = self.get(class_name(owl_object))

        if o_class is None:
            return None

        s_ancestors, o_ancestors = owl_subject.ancestors(), self.get(class_name(owl_object)).ancestors()

        for s_a in s_ancestors:
            for o_a in o_ancestors:
                name: str = role_name(s_a.name, "has", o_a.name)
                if self.get(name) is not None:
                    self.__role_cache[(owl_subject, owl_object)] = name
                    return name

        return None

    def _parse_data_property(self,
                             individual: owl.Thing,
                             data_property: owl.DataProperty,
                             descriptor: Optional[Union[List[Value], Value]]) -> List[Dict[str, any]]:
        """Append data properties to individual"""
        values = getattr(individual, data_property.name)
        values.clear()
        list_length = 0
        errors = []

        if isinstance(descriptor, list):
            for value in descriptor:
                values.append(convert_value(value))
                list_length += 1
        elif descriptor is not None and not isinstance(descriptor, dict):
            values.append(convert_value(descriptor))
            list_length += 1
        else:
            errors.append(descriptor)

        individual.is_a.append(data_property.exactly(list_length))

        return errors

    def _parse_object_property(self,
                               individual: owl.Thing,
                               object_property: owl.ObjectProperty,
                               entity_owl_class_name: str,
                               descriptor: Optional[Union[List[Thing], Thing]]) -> List[Dict[str, any]]:
        """Append data properties to individual"""

        property_list: list = getattr(individual, object_property.name)
        property_list.clear()
        list_length = 0
        errors = []

        if isinstance(descriptor, list):
            for value in descriptor:
                if not isinstance(value, ThingRef):
                    child_individual: owl.Thing = self._entity_to_individual(entity_owl_class_name, value)
                    property_list.append(child_individual)
                    list_length += 1
                else:
                    errors.append(value)

        elif descriptor is not None:
            if not isinstance(descriptor, ThingRef):
                child_individual: owl.Thing = self._entity_to_individual(entity_owl_class_name,
                                                                         descriptor)
                property_list.append(child_individual)
                list_length += 1
            else:
                errors.append(descriptor)
        else:
            errors.append(descriptor)

        individual.is_a.append(object_property.exactly(list_length))

        return errors

    def _merge_individuals(self, new_individual: owl.Thing, old_individual: owl.Thing) -> bool:
        should_add = {}
        new_properties = new_individual.get_properties()
        old_properties = old_individual.get_properties()

        for prop in new_properties:
            if prop in old_properties:
                new_value = set(getattr(new_individual, prop.name))
                old_value = set(getattr(old_individual, prop.name))
                if not self._is_property_equal(new_value, old_value):
                    return False
            else:
                should_add[prop] = getattr(new_individual, prop.name)

        owl.destroy_entity(new_individual)

        for prop, values in should_add.items():
            for value in values:
                getattr(old_individual, prop.name).append(value)

        return True

    def _is_property_equal(self, values_a: Set[Any], values_b: Set[Any]) -> bool:
        return len(values_a.difference(values_b)) == 0
