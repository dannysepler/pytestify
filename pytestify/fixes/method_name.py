from __future__ import annotations

import ast
import re

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
        self.known_rewrites = REWRITES.copy()
        self.to_rewrite: dict[int, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in self.known_rewrites:
            self.to_rewrite[node.lineno - 1] = node.name

        elif not self.keep_casing and not node.name.islower():
            arguments = node.args.args
            # limit rewrites to unit test cases
            if (
                node.name.startswith('test') and
                len(arguments) and arguments[0].arg == 'self'
            ):
                self.to_rewrite[node.lineno - 1] = node.name
                self.known_rewrites[node.name] = to_snake_case(node.name)


def rewrite_method_name(
    contents: str, *, keep_casing: bool = False,
) -> str:
    visitor = Visitor(keep_casing=keep_casing).visit_text(contents)
    content_list = contents.splitlines()
    for line_no, method in visitor.to_rewrite.items():
        line = content_list[line_no]
        line = line.replace(method, visitor.known_rewrites[method])
        content_list[line_no] = line

    return '\n'.join(content_list)
