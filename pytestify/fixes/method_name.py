import ast
from typing import Dict

from pytestify._ast_helpers import NodeVisitor

REWRITES = {
    'setUpClass': 'setup_class',
    'tearDownClass': 'teardown_class',
    'setUp': 'setup_method',
    'tearDown': 'teardown_method',
}


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.methods: Dict[int, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in REWRITES:
            self.methods[node.lineno - 1] = node.name


def rewrite_method_name(contents: str) -> str:
    visitor = Visitor().visit_text(contents)
    content_list = contents.splitlines()
    for line_no, method in visitor.methods.items():
        line = content_list[line_no]
        line = line.replace(method, REWRITES[method])
        content_list[line_no] = line

    return '\n'.join(content_list)
