import ast
import re
from typing import NamedTuple, Optional, Set

from pytestify._ast_helpers import NodeVisitor, imports_pytest_as


class Func(NamedTuple):
    name: Optional[str]
    in_decorator: str = ''

    @property
    def pytest(self) -> str:
        if self.name is None:
            raise SyntaxError
        return self.name

    @property
    def decorator(self) -> Optional[str]:
        return self.in_decorator or self.name


REWRITES = {
    'assertRaises': Func('raises'),
    'assertWarns': Func('warns'),
    'fail': Func('fail'),
    'expectedFailure': Func(None, in_decorator='mark.xfail'),
    'skipTest': Func('skip'),
    'skipIf': Func(None, in_decorator='mark.skipif'),
    'skipUnless(': Func(None, in_decorator='mark.skipif(not '),

    # keep this at end, since it interferes with the others
    'skip': Func('skip', in_decorator='mark.skip'),
}


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.calls: Set[int] = set()

        # strip off punctuation when checking if func name should be rewritten
        self.rewrites = [re.sub(r'[^\w\s]', '', f) for f in REWRITES]

    def visit_Call(self, node: ast.Call) -> None:
        if getattr(node.func, 'attr', None) in self.rewrites:
            self.calls.add(node.lineno - 2)  # decorator
            self.calls.add(node.lineno - 1)  # method call

    def visit_Attribute(self, node: ast.Attribute) -> None:
        '''
        @unittest.expectedFailure() is a call, but
        @unittest.expectedFailure is an attribute
        '''
        if node.attr in self.rewrites:
            self.calls.add(node.lineno - 1)  # decorator


def rewrite_pytest_funcs(contents: str) -> str:
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
        calls = {c + 1 for c in calls}

    pytest_as = pytest_as or 'pytest'
    for line_no in sorted(calls):
        if line_no < 0:
            continue
        line = content_list[line_no]
        for orig, func in REWRITES.items():
            if orig not in line:
                continue

            decorated = line.lstrip().startswith('@')
            replace = func.decorator if decorated else func.pytest

            line = line.replace(f'self.{orig}', f'{pytest_as}.{replace}')
            line = line.replace(f'unittest.{orig}', f'{pytest_as}.{replace}')

        content_list[line_no] = line

    return '\n'.join(content_list)
