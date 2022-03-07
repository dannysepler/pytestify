from __future__ import annotations

import pytest

from pytestify.fixes.imports import add_pytest_import


@pytest.mark.parametrize(
    'line', [
        'pytest.raises(SomeError)',
        'class MyClass:\n'
        '    def test_thing(self):\n'
        '        pytest.raises(SomeError)',
    ],
)
def test_adds_pytest_import(line):
    imports = 'import pytest\n'
    assert add_pytest_import(line) == imports + line


@pytest.mark.parametrize(
    'line', [
        'unrelated_func()',
        'pytest(SomeError)',
        'a.b.c.d(SomeError)',
    ],
)
def test_doesnt_add_pytest_import(line):
    assert add_pytest_import(line) == line


@pytest.mark.parametrize(
    'before, after', [
        (
            'from __future__ import absolute_import\n'
            '\n'
            'pytest.raises(SomeError)',
            'from __future__ import absolute_import\n'
            'import pytest\n'
            '\n'
            'pytest.raises(SomeError)',
        ),
        (
            '""" Some docstring\nblah\nend of docstring"""\n'
            '\n'
            'import abc\n'
            'pytest.blah()',
            '""" Some docstring\nblah\nend of docstring"""\n'
            '\n'
            'import pytest\n'
            'import abc\n'
            'pytest.blah()',
        ),
    ],
)
def test_adds_import_in_a_reasonable_place(before, after):
    assert add_pytest_import(before) == after
