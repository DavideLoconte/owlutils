from __future__ import annotations
from typing import List, Dict, Any


class Node:

    def __init__(self,
                 key: str,
                 value: str,
                 start: int,
                 end: int = None,
                 children: List[Node] = None,
                 parent: Node = None,
                 filename: str = None):

        if children is None:
            children = []

        self.key = key
        self.value = value
        self.children = children
        self.parent = parent
        self.start = start
        self.end = end if end is not None else start
        self.filename = filename if filename is not None else ''

        if len(self.children) == 0:
            for child in self.children:
                child.parent = self

    @property
    def depth(self):
        if not self.parent:
            return 0
        else:
            return self.parent.depth + 1

    def __str__(self) -> str:
        result: List[str] = [f'Node: ({self.key}, {self.value}) {"{"}']
        for child in self.children:
            result.append(str(child))
        result.append('}')
        return '\n'.join(result)


class Root(Node):
    def __init__(self,
                 key: str,
                 value: str,
                 start: int,
                 end: int = None,
                 children: List[Node] = None):
        super().__init__(key, value, start, end, children)

    @property
    def depth(self):
        return 0

    def __str__(self) -> str:
        result = [f'Root: ({self.key}, {self.value}) {"{"}']
        for child in self.children:
            result.append(f'{child}')
        result.append('}')
        return '\n'.join(result)


class Leaf(Node):

    def __init__(self,
                 key: str,
                 value: str,
                 start: int):
        super().__init__(key, value, start)

    def __str__(self) -> str:
        return f'Leaf: ({self.key}, {self.value})'
