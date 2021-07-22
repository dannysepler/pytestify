import ast
import warnings
from typing import Any


def ast_parse(contents: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents)


def is_valid_syntax(contents: str) -> bool:
    try:
        ast_parse(contents)
    except SyntaxError:
        return False
    return True


class NodeVisitor(ast.NodeVisitor):
    def visit_text(self, contents: str) -> Any:
        self.visit(ast_parse(contents))
        return self


class FindImportName(NodeVisitor):
    def __init__(self, search: str):
        self.search = search
        self.imports = False

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == self.search:
                self.imports = True


def imports_pytest(contents: str) -> bool:
    visitor = FindImportName('pytest').visit_text(contents)
    return visitor.imports
