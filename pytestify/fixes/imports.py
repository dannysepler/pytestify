import ast

from pytestify._ast_helpers import NodeVisitor, imports_pytest


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.uses_pytest_func: bool = False

    def visit_Call(self, node: ast.Call) -> None:
        print(ast.dump(node))
        val = getattr(node.func, 'value', None)
        if val and val.id == 'pytest':
            self.uses_pytest_func = True


def add_pytest_import(contents: str) -> str:
    imports = imports_pytest(contents)
    if imports:
        return contents

    visitor = Visitor().visit_text(contents)
    if visitor.uses_pytest_func and not imports:
        content_list = contents.splitlines()
        non_future_line = next(
            i for i, line in enumerate(content_list)
            if not line.startswith('from __future__')
        )
        content_list.insert(non_future_line, 'import pytest')
        return '\n'.join(content_list)
    else:
        return contents
