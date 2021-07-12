import ast
from typing import List, NamedTuple

from pytestify._ast_helpers import elems_of_type

REWRITES = {
    'setUp': 'setup_method',
    'tearDown': 'teardown_method',
}


class Method(NamedTuple):
    name: str
    line: int


def get_selected_methods(contents: str) -> List[Method]:
    methods = []
    for method in elems_of_type(contents, ast.FunctionDef):
        if method.name in REWRITES.keys():
            line = method.lineno - 1
            methods.append(Method(method.name, line))
    return methods


def rewrite_method_name(contents: str) -> str:
    methods = get_selected_methods(contents)
    content_list = contents.splitlines()
    for m in methods:
        line = content_list[m.line]
        line = line.replace(m.name, REWRITES[m.name])
        content_list[m.line] = line

    return '\n'.join(content_list)
