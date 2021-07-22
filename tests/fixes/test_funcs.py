import pytest

from pytestify.fixes.funcs import rewrite_pytest_funcs


@pytest.mark.parametrize(
    'before, after', [
        ('self.assertRaises(Exc)', 'pytest.raises(Exc)'),
        ('with self.assertRaises(Exc): pass', 'with pytest.raises(Exc): pass'),
        (
            'with self.assertRaises(Exc) as e: pass',
            'with pytest.raises(Exc) as e: pass',
        ),
        ('self.assertWarns(Exc)', 'pytest.warns(Exc)'),
        ('with self.assertWarns(Exc): pass', 'with pytest.warns(Exc): pass'),
        ('self.fail("some reason")', 'pytest.fail("some reason")'),
        (
            '@unittest.expectedFailure\n'
            'def blah(): pass',
            '@pytest.mark.xfail\n'
            'def blah(): pass',
        ),
        (
            '@unittest.skip("some reason")\n'
            'def blah(): pass',
            '@pytest.mark.skip("some reason")\n'
            'def blah(): pass',
        ),
        (
            '@unittest.skipIf(some_bool)\n'
            'def blah(): pass',
            '@pytest.mark.skipif(some_bool)\n'
            'def blah(): pass',
        ),
        ('unittest.skipTest("Some reason")', 'pytest.skip("Some reason")'),
        (
            '@unittest.skipUnless(some_bool)\n'
            'def blah(): pass',
            '@pytest.mark.skipif(not some_bool)\n'
            'def blah(): pass',
        ),
    ],
)
def test_rewrite_pytest_funcs(before, after):
    assert rewrite_pytest_funcs(before) == after


@pytest.mark.parametrize(
    'line', [
        '# self.assertRaises(SomeException):',
        '# self.assertWarns(SomeException):',
    ],
)
def test_doesnt_rewrite_pytest_funcs(line):
    assert rewrite_pytest_funcs(line) == line


@pytest.mark.parametrize(
    'line', [
        'unittest.expectedFailure',
        'unittest.skipIf(some_bool)',
        'unittest.skipUnless(some_bool)',
    ],
)
def test_syntax_error_on_bad_funcs(line):
    with pytest.raises(SyntaxError):
        rewrite_pytest_funcs(line)
