import ast
from typing import List

from pytestify._ast_helpers import elems_of_type, imports_pytest_as

REWRITES = {
    'assertRaises': 'raises',
    'assertWarns': 'warns',
}


def get_calls(contents: str) -> List[int]:
    locations = []
    calls = elems_of_type(contents, ast.Call)
    calls += [
        expr.value for expr in elems_of_type(contents, ast.Expr)
        if isinstance(expr.value, ast.Call)
    ]
    for call in calls:
        if getattr(call.func, 'attr', None) in REWRITES.keys():
            locations.append(call.lineno - 1)
    return locations


def rewrite_raises(contents: str) -> str:
    calls = get_calls(contents)
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
