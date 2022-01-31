#pylint: disable=logging-fstring-interpolation
import sys

import owlready2
import logging

from typing import Dict, Set, List

from owlready2.base import OwlReadyDupplicatedNameWarning

from yang2owl.owl.interface import create_class, create_data_property, create_object_property
from yang2owl.owl.naming import suffix, prefix, class_name, role_name
from yang2owl.yang.analyzer import AbsNode


class OntologyFactory:
    """Class which generates the ontologies from the abstract tree"""
    def __init__(self, namespace, modules: List[AbsNode]):
        self.ontology: owlready2.Ontology = owlready2.get_ontology(namespace)
        self.namespaces: Dict[str, str] = {}
        self.modules: Dict[str, AbsNode] = {}
        self.imports: Dict[str, AbsNode] = {}
        self.warnings: Dict[str, bool] = {'notification': False, 'rpc': False, 'augment': False}

        for module in [x for x in modules if x.key == 'module']:
            self.namespaces[module.metadata['prefix']] = module.metadata['namespace']
            self.modules[module.metadata['prefix']] = module

        for submodule in [x for x in modules if x.key == 'submodule']:
            belongs_to = submodule.get_children('belongs-to')[0]
            for child in submodule.children:
                self.modules[belongs_to.metadata['prefix']].children.append(child)
                child.parent = self.modules[belongs_to.metadata['prefix']]

        self.current_prefix = None

    def build(self, targets: Set[str] = None):
        """Build the ontology. It generates the hierarchy starting from targets"""
        self.__process_augment_nodes()

        if len(targets) == 0 or targets is None:
            targets = {x.value for x in self.modules.values()}

        for module_prefix, module in self.modules.items():
            self.current_prefix = module_prefix
            self.imports = self.__import_modules(module)

            if module.value in targets:
                self.__build([x for x in module.children])

        for node, status in self.warnings.items():
            if status:
                print('Node {} translation is not supported'.format(node), file=sys.stderr)

        return self.ontology

    def __build(self, nodes: List[AbsNode]):
        """Recursively build ontology"""
        for node in nodes:
            self.__traverse_node(node)

    def __traverse_node(self, node: AbsNode):
        """Traverse a node of the ABSTree"""
        ignore = {
            'revision',
            'import',
            'must',
            'when',
            'grouping',
            'typedef',
            'identity',
            'belongs-to',
            'augment'
        }

        if node.key == 'leaf':
            self.__process_leaf(node)
        elif node.key == 'leaf-list':
            self.__process_leaf_list(node)
        elif node.key == 'list':
            self.__process_list(node)
        elif node.key == 'container':
            self.__process_container(node)
        elif node.key == 'uses':
            self.__process_uses(node)
        elif node.key == 'choice':
            self.__process_choice(node)
        elif node.key == 'include':
            self.__process_include(node)
        elif node.key in ignore:
            pass
        else:
            if node.key in self.warnings:
                self.warnings[node.key] = True
            else:
                logging.error(f'Unhandeld {node.key} {node.value}')

    def __process_leaf(self, leaf: AbsNode):
        """Translates a leaf node to a data property"""

        for child in leaf.get_children('type'):
            if child.value == 'leafref':
                self.__process_leafref(leaf, child)

        role = create_data_property(
            self.ontology,
            role_name(leaf.parent.value, 'has', leaf.value),
            comment=leaf.metadata.get('description'),
            domain=leaf.parent.owl_class
        )

        if 'key' in leaf.metadata:
            role.isDefinedBy.append(leaf.metadata.get('key'))

        # if leaf.parent.owl_class != owlready2.Thing:
        #     if leaf.metadata.get('mandatory', 'false') == 'true':
        #         leaf.parent.owl_class.is_a.append(role.min(1))

    def __process_leaf_list(self, leaf: AbsNode):
        """Translates a leaf list node to a data property"""
        role = create_data_property(
            self.ontology,
            role_name(leaf.parent.value, 'has', leaf.value),
            comment=leaf.metadata.get('description'),
            domain=leaf.parent.owl_class
        )

        if 'key' in leaf.metadata:
            role.isDefinedBy.append(leaf.metadata.get('key'))

        # if leaf.parent.owl_class != owlready2.Thing:
        #     leaf.parent.owl_class.is_a.append(role.min(int(leaf.metadata.get('min-elements', 0))))

    def __process_container(self, container: AbsNode):
        """Translates a container node to a OWL Class"""
        container.owl_class = create_class(
            self.ontology,
            class_name(container.value),
            super_class=owlready2.Thing,
            comment=container.metadata.get('description'),
        )

        if 'key' in container.metadata:
            container.owl_class.isDefinedBy.append(container.metadata.get('key'))

        if container.parent.owl_class != owlready2.Thing:
            role = create_object_property(
                self.ontology,
                role_name(container.parent.value, 'has', container.value),
                domain=container.parent.owl_class,
                range=container.owl_class
            )
            container.parent.owl_class.is_a.append(role.max(1, container.owl_class))

        for x in container.children:
            self.__traverse_node(x)

    def __process_list(self, list_node: AbsNode):
        """Translates a list node to a OWL Class"""

        list_node.owl_class = create_class(
            self.ontology,
            class_name(list_node.value),
            comment=list_node.metadata.get('description'),
            super_class=owlready2.Thing,
        )

        if 'key' in list_node.metadata:
            list_node.owl_class.isDefinedBy.append(list_node.metadata.get('key'))

        if list_node.parent.owl_class != owlready2.Thing:
            role = create_object_property(
                self.ontology,
                role_name(list_node.parent.value, 'has', list_node.value),
                domain=list_node.parent.owl_class,
                range=list_node.owl_class
            )
            # list_node.parent.owl_class.is_a.append(role.min(int(list_node.metadata.get('min-elements', 0))))

        for child in list_node.children:
            self.__traverse_node(child)

    def __process_uses(self, uses: AbsNode):
        """Import grouping node referenced by the uses node"""
        grouping = self.__find_grouping(uses)

        if grouping is None:
            logging.error('Cannot resolve grouping ' + self.current_prefix + ':' + uses.value)
            return None

        parent = grouping.parent
        for child in grouping.children:
            child.parent = uses.parent
            self.__traverse_node(child)
            child.parent = parent

    def __find_grouping(self, uses: AbsNode):
        """Find the grouping node referenced by the uses node"""
        name = uses.value
        uses_prefix = self.current_prefix

        if uses.root.key == 'module':
            uses_prefix = uses.root.metadata['prefix']
        elif uses.root.key == 'submodule':
            uses_prefix = uses.root.get_children('belongs-to')[0].metadata['prefix']

        grouping_name = suffix(name)
        grouping_prefix = uses_prefix if len(prefix(name).strip()) == 0 else prefix(name)
        groupings = []

        for imported_module in self.imports.get(grouping_prefix, []):
            for imported_grouping in imported_module.get_children('grouping'):
                groupings.append(imported_grouping)
        for grouping in groupings:
            if grouping.value == grouping_name:
                return grouping

        groupings = [x for x in self.modules[grouping_prefix].get_children("grouping")]

        for grouping in groupings:
            if grouping.value == grouping_name:
                return grouping

        return None

    def __process_choice(self, choice: AbsNode):
        """Translates the choice node accordingly to the different choices"""
        choice.owl_class = choice.owl_superclass

        for child in choice.children:
            if child.key == 'container':
                child.owl_class = create_class(
                    self.ontology,
                    class_name(child.value),
                    super_class=choice.owl_class,
                    comment=child.metadata.get('description')
                )

                if 'key' in child.metadata:
                    child.owl_class.isDefinedBy.append(child.metadata['key'])

                if choice.parent.owl_class != owlready2.Thing:
                    role = create_object_property(
                        self.ontology,
                        role_name(choice.parent.value, 'has', choice.value),
                        domain=choice.parent.owl_class,
                        range=choice.owl_class
                    )
                    choice.parent.owl_class.is_a.append(role.max(1, choice.owl_class))

                for next_child in child.children:
                    self.__traverse_node(next_child)

            elif child.key == 'case':
                temp = choice.value
                choice.value = choice.parent.value
                self.__process_case(child)
                choice.value = temp

            elif child.key == 'leaf':
                temp = choice.value
                choice.value = choice.parent.value
                self.__process_leaf(child)
                choice.value = temp

            elif child.key == 'leaf-list':
                temp = choice.value
                choice.value = choice.parent.value
                self.__process_leaf_list(child)
                choice.value = temp

            elif child.key == 'list':
                child.owl_class = create_class(
                    self.ontology,
                    class_name(child.value),
                    super_class=choice.owl_class,
                    comment=child.metadata.get('description')
                )

                if 'key' in child.metadata:
                    child.owl_class.isDefinedBy.append(child.metadata.get('key'))

                if choice.parent.owl_class != owlready2.Thing:

                    role = create_object_property(
                        self.ontology,
                        role_name(choice.parent.value, 'has', choice.value),
                        domain=choice.parent.owl_class,
                        range=choice.owl_class
                    )
                    # choice.parent.owl_class.is_a.append(role.min(int(choice.metadata.get('min-elements', 0))))

                for next_child in child.children:
                    self.__traverse_node(next_child)

    def __import_modules(self, module: AbsNode):
        """Import an external module"""
        result = {}
        for import_stmt in module.get_children('import'):
            temp = []
            module_name = import_stmt.value
            module_prefix = import_stmt.metadata['prefix']
            for imported_module in self.modules.values():
                if imported_module.value == module_name:
                    temp.append(imported_module)
            result[module_prefix] = temp
        return result

    def __process_include(self, node):
        """Include modules are not implemented"""

    def __process_case(self, case):
        """Cases nodes are not implemented"""
        raise NotImplementedError

    def __process_augment_nodes(self):
        """Add schema nodes to target nodes accordingly to the augment nodes"""
        augment_nodes: List[AbsNode] = []

        for module in self.modules.values():
            for augment_node in module.get_children('augment'):
                augment_nodes.append(augment_node)

        augment_nodes.sort(key=lambda x: len(x.value[1:].split('/')))

        for augment_node in augment_nodes:
            self.__process_augment(augment_node)

    def __process_augment(self, augment_node):
        """Process a single augment node to augment a existing schema tree node"""
        valid_targets = {'container', 'list', 'choice', 'case', 'notification', 'grouping'}
        target_node = self.__resolve_name(augment_node.value)
        augment_node_value = augment_node.value.split('/')[-1].split(':')[-1]

        if (target_node.key not in valid_targets or \
            target_node.value != augment_node_value) and \
            target_node.key not in ['input', 'output']:
            print("Error converting " + str(target_node))
            raise SyntaxError

        for child in augment_node.children:
            child.parent = target_node
            target_node.children.append(child)

    def __resolve_name(self, name: str) -> AbsNode:

        if name[0] != '/':
            raise SyntaxError

        path = name[1:].split('/')
        target_node = self.__get_module_from_path(path)

        if target_node is None:
            print("Cannot resolve " + name)
            raise SyntaxError

        for node_id in path:
            for child in target_node.children:
                if node_id == f'{child.root.value}:{child.value}' or \
                   node_id == f'{child.root.value}:{child.key}':
                    target_node = child
                    break
            else:
                for uses in target_node.get_children('uses'):
                    grouping = self.__find_grouping(uses)
                    for child in grouping.children:
                        if node_id == f'{child.root.value}:{child.value}' or\
                           node_id == f'{child.root.value}:{child.key}':
                           target_node = child
        return target_node

    def __get_module_from_path(self, path) -> AbsNode:
        module_name = prefix(path[0])
        for _, module in self.modules.items():
            if module.value == module_name:
                return module
        return None

    def __process_leafref(self, leaf: AbsNode, leafref: AbsNode):
        pass