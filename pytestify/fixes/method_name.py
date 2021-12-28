import ast
import re
from typing import Dict

from pytestify._ast_helpers import NodeVisitor

REWRITES = {
    'setUpClass': 'setup_class',
    'tearDownClass': 'teardown_class',
    'setUp': 'setup_method',
    'tearDown': 'teardown_method',
}


def to_snake_case(s: str) -> str:
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s).lower()


class Visitor(NodeVisitor):
    def __init__(self, *, keep_casing: bool = False) -> None:
        self.keep_casing = keep_casing
        self.rewrites = REWRITES.copy()
        self.methods: Dict[int, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in self.rewrites:
            self.methods[node.lineno - 1] = node.name
        elif not self.keep_casing and not node.name.islower():
            self.methods[node.lineno - 1] = node.name
            self.rewrites[node.name] = to_snake_case(node.name)


def rewrite_method_name(
    contents: str, *, keep_casing: bool = False,
) -> str:
    visitor = Visitor(keep_casing=keep_casing).visit_text(contents)
    content_list = contents.splitlines()
    for line_no, method in visitor.methods.items():
        line = content_list[line_no]
        line = line.replace(method, visitor.rewrites[method])
        content_list[line_no] = line

    return '\n'.join(content_list)
