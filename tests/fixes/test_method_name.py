import pytest

from pytestify.fixes.method_name import rewrite_method_name


@pytest.mark.parametrize(
    'before, after', [
        ('def setUp(self): pass', 'def setup_method(self): pass'),
        ('def tearDown(self): pass', 'def teardown_method(self): pass'),
    ],
)
def test_rewrite_method_name(before, after):
    assert rewrite_method_name(before) == after


@pytest.mark.parametrize(
    'line', [
        '# def setUp(self): pass',
        'def setup(self): pass',
    ],
)
def test_doesnt_rewrite_method_name(line):
    assert rewrite_method_name(line) == line
