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
    ],
)
def test_doesnt_add_pytest_import(line):
    assert add_pytest_import(line) == line


def test_adds_import_below_future():
    before = (
        'from __future__ import absolute_import\n'
        '\n'
        'pytest.raises(SomeError)'
    )
    after = (
        'from __future__ import absolute_import\n'
        'import pytest\n'
        '\n'
        'pytest.raises(SomeError)'
    )
    assert add_pytest_import(before) == after
