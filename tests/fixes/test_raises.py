import pytest

from pytestify.fixes.raises import rewrite_raises


@pytest.mark.parametrize(
    'before, after', [
        ('self.assertRaises(Exc)', 'pytest.raises(Exc)'),
        ('with self.assertRaises(Exc): pass', 'with pytest.raises(Exc): pass'),
        (
            'with self.assertRaises(Exc) as e: pass',
            'with pytest.raises(Exc) as e: pass',
        ),
    ],
)
def test_rewrite_raises(before, after):
    imports = 'import pytest\n'
    assert rewrite_raises(imports + before) == imports + after


@pytest.mark.parametrize(
    'before, after', [
        (
            'self.assertRaises(Exc)',
            'import pytest\n'
            'pytest.raises(Exc)',
        ),
        (
            'import pytest\n'
            'self.assertRaises(Exc)',
            'import pytest\n'
            'pytest.raises(Exc)',
        ),
        (
            'import pytest as pt\n'
            'self.assertRaises(Exc)',
            'import pytest as pt\n'
            'pt.raises(Exc)',
        ),
    ],
)
def test_adds_import_when_necessary(before, after):
    assert rewrite_raises(before) == after


@pytest.mark.parametrize(
    'line', [
        '# self.assertRaises(SomeException):',
    ],
)
def test_doesnt_rewrite_raises(line):
    assert rewrite_raises(line) == line
