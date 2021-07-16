import ast
from typing import List

from pytestify._ast_helpers import NodeVisitor, imports_pytest_as

REWRITES = {
    'assertRaises': 'raises',
    'assertWarns': 'warns',
}


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.calls: List[int] = []

    def visit_Call(self, node: ast.Call) -> None:
        if getattr(node.func, 'attr', None) in REWRITES:
            self.calls.append(node.lineno - 1)


def rewrite_raises(contents: str) -> str:
    visitor = Visitor().visit_text(contents)
    calls = visitor.calls
    content_list = contents.splitlines()
    pytest_as = imports_pytest_as(contents)
    if calls and not pytest_as:
        non_future_line = next(
            i for i, line in enumerate(content_list)
            if line.strip() and not line.startswith('from __future__')
        )
        content_list.insert(non_future_line, 'import pytest')
        calls = [c + 1 for c in calls]

    pytest_as = pytest_as or 'pytest'
    for line_no in calls:
        line = content_list[line_no]
        for unit_impl, pytest_impl in REWRITES.items():
            if unit_impl in line:
                line = line.replace(
                    f'self.{unit_impl}', f'{pytest_as}.{pytest_impl}',
                )
        content_list[line_no] = line

    return '\n'.join(content_list)
