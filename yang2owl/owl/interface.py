import types
import owlready2 as owl


def create_class(ontology: owl.Ontology,
                 class_name: str,
                 super_class: type = owl.Thing,
                 comment: str = None,
                 label: str = None) -> type:
    with ontology:
        new_class = get_class(ontology, class_name)
        if new_class is None:
            new_class = types.new_class(class_name, (super_class,))
        if comment is not None:
            new_class.comment = comment
        if label is not None:
            new_class.label = label
        # new_class.isDefinedBy = "yang2owl"
    return getattr(ontology, class_name)


def create_data_property(ontology: owl.Ontology,
                         property_name: str,
                         domain: type = None,
                         comment: str = None,
                         label: str = None) -> type:
    with ontology:
        new_role = types.new_class(property_name, (owl.DataProperty,))
        # new_role.isDefinedBy = "yang2owl"
        if domain is not None:
            new_role.domain = domain
        if comment is not None:
            new_role.comment = comment
        if label is not None:
            new_role.label = label
        return new_role


def create_object_property(ontology: owl.Ontology,
                           property_name: str,
                           domain: type = None,
                           range: type = None,
                           comment: str = None,
                           label: str = None) -> type:
    with ontology:
        new_role = types.new_class(property_name, (owl.ObjectProperty,))
        # new_role.isDefinedBy = "yang2owl"
        if domain is not None:
            new_role.domain = domain
        if range is not None:
            new_role.range = range
        if comment is not None:
            new_role.comment = comment
        if label is not None:
            new_role.label = label
        return new_role


def get_class(ontology: owl.Ontology, class_name) -> owl.ThingClass:
    return ontology.__getattr__(class_name)
