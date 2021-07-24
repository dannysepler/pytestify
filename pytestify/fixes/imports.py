import ast

from pytestify._ast_helpers import NodeVisitor, imports_pytest


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.uses_pytest_func: bool = False

    def visit_Call(self, node: ast.Call) -> None:
        child = getattr(node.func, 'value', None)
        while child:
            if getattr(child, 'id', None) == 'pytest':
                self.uses_pytest_func = True
                return
            child = getattr(child, 'value', None)


def add_pytest_import(contents: str) -> str:
    if 'pytest' not in contents:
        return contents
    imports = imports_pytest(contents)
    if imports:
        return contents

    visitor = Visitor().visit_text(contents)
    if visitor.uses_pytest_func and not imports:
        content_list = contents.splitlines()
        import_line = 0
        for i, line in enumerate(content_list):
            if line.startswith('from __future__'):
                import_line = i + 1
            elif line.startswith(('from', 'import')):
                import_line = i
                break

        content_list.insert(import_line, 'import pytest')
        return '\n'.join(content_list)
    else:
        return contents
