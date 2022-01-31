import logging

from typing import Dict, Set, List, Tuple
from .tree import Root, Node

allow_unknown_stmts = False

root_stmts: List[str] = ['module', 'submodule']

single_stmts: Dict[str, Set[str]] = {
    'typedef': {'type'},
    'import': {'prefix'},
    'belongs-to': {'prefix'},
    'leaf': {'type'},
    'module': {'namespace', 'prefix'},
    'submodule': {'yang-version', 'belongs-to'},
    'leaf-list': {'type'}
}

any_stmts: Dict[str, Set[str]] = {
    'type': {'type', 'enum'},
    'enum': {'if-feature'},
    'bit': {'if-feature'},
    'case': {'if-feature', 'container', 'list', 'leaf-list', 'list', 'anydata', 'anyxml', 'uses'},
    'identity': {'if-feature', 'base'},
    'leaf': {'if-feature', 'must'},
    'choice': {'if-feature', 'case', 'choice', 'container', 'leaf', 'leaf-list', 'list', 'anydata', 'anyxml'},
    'module': {'yang-version', 'import', 'include', 'revision', 'extension', 'feature', 'identity', 'typedef', 'grouping', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses',
        'augment', 'notification', 'deviation', 'rpc', 'notification'},
    'submodule': {'import', 'include', 'revision', 'extension', 'feature', 'identity', 'typedef', 'grouping', 'container', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses',
        'augment', 'notification', 'deviation', 'rpc', 'notification'},
    'container': {'action', 'notification', 'typedef', 'grouping', 'if-feature', 'must', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'leaf-list': {'if-feature', 'must', 'default'},
    'grouping': {'typedef', 'grouping', 'action', 'notification', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'uses': {'if-feature', 'refine', 'augment'},
    'list': {'type', 'if-feature', 'must', 'unique', 'typedef', 'grouping', 'action', 'notification', 'container', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'deviate': {'must', 'unique', 'default'},
    'augment': {'if-feature', 'case', 'action', 'notification', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'action': {'typedef', 'grouping'},
    'input': {'must', 'typedef', 'grouping', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'output': {'must', 'typedef', 'grouping', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'anydata': {'if-feature', 'must'},
    'anyxml': {'if-feature', 'must'},
    'feature': {'if-feature'},
    'rpc': {'if-feature', 'grouping', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
    'notification': {'if-feature', 'must', 'typedef', 'grouping', 'container', 'leaf', 'leaf-list', 'list', 'choice', 'anydata', 'anyxml', 'uses'},
}

opt_stmts: Dict[str, Set[str]] = {
    'range': {'error-message', 'error-app-tag', 'description', 'reference'},
    'length': {'error-message', 'error-app-tag', 'description', 'reference'},
    'pattern': {'error-message', 'error-app-tag', 'description', 'reference'},
    'type': {'range', 'fraction-digits', 'length', 'pattern', 'path', 'require', 'base', 'bit', 'length'},
    'enum': {'value', 'status', 'description', 'reference'},
    'bit': {'description', 'reference', 'status', 'position'},
    'include': {'revision-date', 'description', 'reference'},
    'identity': {'status', 'description', 'reference'},
    'revision': {'description', 'reference'},
    'typedef': {'status', 'description', 'reference', 'default', 'units'},
    'when': {'description', 'reference'},
    'must': {'error-message', 'error-app-tag', 'description', 'reference'},
    'import': {'revision', 'description', 'reference'},
    'leaf': {'units', 'default', 'config', 'mandatory', 'status', 'description', 'reference', 'when'},
    'choice': {'when', 'default', 'config', 'mandatory', 'status', 'description', 'reference'},
    'case': {'when', 'status', 'description', 'reference'},
    'module': {'organization', 'contact', 'description', 'reference'},
    'submodule': {'organization', 'contact', 'description', 'reference'},
    'container': {'when', 'presence', 'config', 'status', 'description', 'reference'},
    'leaf-list': {'when', 'units', 'config', 'min-elements', 'max-elements', 'ordered-by', 'status', 'description', 'reference'},
    'grouping': {'status', 'description', 'reference'},
    'uses': {'when', 'status', 'description', 'reference'},
    'list': {'when', 'key', 'config', 'min-elements', 'max-elements', 'ordered-by', 'status', 'description', 'reference'},
    'deviation': {'description', 'reference'},
    'deviate': {'type', 'units', 'default', 'config', 'mandatory', 'min-elements', 'max-elements'},
    'augment': {'when', 'status', 'description', 'reference'},
    'action': {'status', 'description', 'reference', 'input', 'output'},
    'anydata': {'when', 'config', 'mandatory', 'status', 'description', 'reference'},
    'anyxml': {'when', 'config', 'mandatory', 'status', 'description', 'reference'},
    'feature': {'stauts', 'description', 'reference'},
    'rpc': {'status', 'description', 'reference', 'input', 'output'},
    'notification': {'status', 'description', 'reference'}
}

multiple_stmts: Dict[str, Set[str]] = {
    'deviation': {'deviate'}
}

leaf_stmts: Set[str] = {
    'organization',
    'ordered-by',
    'yang-version',
    'max-elements',
    'error-message',
    'error-app-tag',
    'description',
    'reference',
    'fraction-digits',
    'value',
    'status',
    'path',
    'require-instance',
    'position',
    'revision-date',
    'base',
    'prefix',
    'default',
    'units',
    'presence',
    'namespace',
    'key',
    'min-elements',
    'ordered-by',
    'config',
    'unique',
    'mandatory',
    'contact',
    'if-feature'
}

value_restrictions: Dict[str, Set[str]] = {

}


def check(tree: Root) -> List[str]:

    logging.debug('Starting syntax analysis')
    error_list: List[Tuple[int, str]] = []
    if root_stmts is not None and tree.key not in root_stmts:
        error_list.append(
            (int(tree.start), f'Module starts with {tree.key}, expected one of {root_stmts}'))

    for error in __syntax_check(tree):
        error_list.append(error)

    error_list.sort(key=lambda x: x[0])
    errors = [f'{error[0]}: {error[1]}' for error in error_list]
    tree.errors = errors
    return errors


def __syntax_check(node: Node) -> List[Tuple[int, str]]:

    error_list: List[Tuple[int, str]] = []
    node_children: Dict[str, int] = {}
    for child in node.children:

        if child.key not in node_children:
            node_children[child.key] = 1
        else:
            node_children[child.key] += 1

        if len(child.children) != 0:
            for error in __syntax_check(child):
                error_list.append(error)
            if child.key in leaf_stmts:
                error_list.append((child.start, f'{child.key} statement should not contain other statements'))

    checked_node_children: Set[str] = set(node_children.keys())


    if node.key in value_restrictions and node.value not in value_restrictions[node.key]:
        error_list.append((
            node.start,
            f'Unexpected {node.value} value, maybe you meant one of these: {list(value_restrictions[node.key])}'
        ))

    # One and only one:
    for key in single_stmts.get(node.key, {}):
        if key not in node_children:
            error_list.append((node.start, f'Missing {key} statement in {node.key} {node.value}'))
        elif node_children.get(key) > 1:
            error_list.append((node.start, f'Duplicate {key} statement in {node.key} {node.value}'))
        checked_node_children.discard(key)

    # One or more
    for key in multiple_stmts.get(node.key, {}):
        if key not in node_children:
            error_list.append((node.start, f'Missing {key} statement in {node.key} {node.value}'))
        checked_node_children.discard(key)

    # Optional stmts
    for key in opt_stmts.get(node.key, {}):
        if node_children.get(key, 1) > 1:
            error_list.append((node.start, f'Duplicate {key} statement in {node.key} {node.value}'))
        checked_node_children.discard(key)

    # Any Stmt
    for key in any_stmts.get(node.key, {}):
        checked_node_children.discard(key)

    # Every node in node children is illegal
    for key in checked_node_children:
        error_list.append((node.start, f'Illegal statement {key} in {node.key} {node.value}'))

    if not allow_unknown_stmts:
        key = node.key
        if key not in single_stmts.keys() and key not in multiple_stmts.keys() and key not in opt_stmts.keys() and key not in any_stmts.keys():
            error_list.append((node.start, f'Unknown {key} statement'))

    return error_list

