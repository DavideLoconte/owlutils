from typing import Dict, Set, Union, List

import owlready2

from yang2owl.yang.tree import Node
from yang2owl.yang.structure import leaf_stmts



class AbsNode:

    def __init__(self, key, value=None, metadata=None, children=None, parent=None):
        self.key = key
        self.value = value
        self.parent = parent

        if metadata is None:
            self.metadata = {}
        else:
            self.metadata = metadata

        if children is None:
            self.children = []
        else:
            self.children = children

        self.owl_class: type = owlready2.Thing
        self.in_owl_roles_ranges: Set[str] = set()
        self.in_owl_role_domains: Set[str] = set()
        self.root = self.__root()

        self.nodeid = '{}:{}'.format(self.root.value, self.value)

    @property
    def depth(self):
        if self.parent is None:
            return 0
        else:
            return self.parent.depth + 1

    def __root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @property
    def descendents(self):
        descendents = []
        if len(self.children) != 0:
            for child in self.children:
                descendents = descendents + child.descendents
        return descendents + self.children

    @property
    def owl_superclass(self):
        return self.parent.owl_class if self.parent.owl_class is not None else owlready2.Thing

    def get_children(self, key: str):
        return [x for x in self.children if x.key == key]

    def get_descendents(self, key: str):
        return [x for x in self.descendents if x.key == key]

    def child_from_value(self, value: str):
        return [x for x in self.children if x.value == value]

    def __str__(self) -> str:
        tabs = ''.join(['\t' for _ in range(self.depth)])
        metadata_str = '' if len(self.metadata) == 0 else str(self.metadata)
        result: List[str] = [f'{tabs} {self.key}: {self.value} {metadata_str}']
        for child in self.children:
            result.append(str(child))
        return '\n'.join(result)

    def __hash__(self):
        return self.__str__().__hash__()


def analyze(stree: Node, parent=None) -> AbsNode:
    """Create the abstract tree starting from the syntax tree"""
    metadata: Dict[str, Union[Set[str], str]] = {}
    children = []
    result = AbsNode(stree.key, stree.value, metadata, children, parent)
    result.metadata['lines'] = f'{stree.start}:{stree.end}'
    for child in stree.children:
        if child.key in leaf_stmts:
            if child.key not in metadata:
                metadata[child.key] = set()
            metadata[child.key].add(child.value)
        else:
            children.append(analyze(child, parent=result))
    for key in metadata.keys():
        if len(metadata.get(key, {})) == 1:
            metadata[key] = metadata[key].pop()
    return result
