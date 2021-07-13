import ast
from typing import List

from pytestify._ast_helpers import elems_of_type, imports_pytest_as


def get_raises(contents: str) -> List[int]:
    locations = []
    calls = elems_of_type(contents, ast.Call)
    calls += [
        expr.value for expr in elems_of_type(contents, ast.Expr)
        if isinstance(expr.value, ast.Call)
    ]
    for call in calls:
        if getattr(call.func, 'attr', None) == 'assertRaises':
            locations.append(call.lineno - 1)
    return locations


def rewrite_raises(contents: str) -> str:
    calls = get_raises(contents)
    content_list = contents.splitlines()
    pytest_as = imports_pytest_as(contents)
    if calls and not pytest_as:
        content_list.insert(0, 'import pytest')
        calls = [c + 1 for c in calls]

    pytest_as = pytest_as or 'pytest'
    for line_no in calls:
        line = content_list[line_no]
        line = line.replace('self.assertRaises', f'{pytest_as}.raises')
        content_list[line_no] = line

    return '\n'.join(content_list)
