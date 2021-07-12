import pytest

from pytestify.fixes.asserts import rewrite_asserts


@pytest.mark.parametrize(
    'before, after', [
        # unary asserts
        ('self.assertTrue(True)', 'assert True'),
        ('self.assertFalse(False)', 'assert not False'),
        ('self.assertIsNone(a)', 'assert a is None'),
        ('self.assertIsNotNone(a)', 'assert a is not None'),

        # binary asserts
        ('self.assertEquals(1, 1)', 'assert 1 == 1'),
        ('self.assertEqual(1, 1)', 'assert 1 == 1'),
        ('self.assertNotEqual(1, 2)', 'assert 1 != 2'),
        ('self.assertListEqual([1], [1])', 'assert [1] == [1]'),
        ('self.assertIs(a, b)', 'assert a is b'),
        ('self.assertIsNot(a, b)', 'assert a is not b'),
        ('self.assertIn(a, b)', 'assert a in b'),
        ('self.assertNotIn(a, b)', 'assert a not in b'),
        ('self.assertGreater(a, b)', 'assert a > b'),
        ('self.assertLess(a, b)', 'assert a < b'),
        ('self.assertGreaterEqual(a, b)', 'assert a >= b'),
        ('self.assertLessEqual(a, b)', 'assert a <= b'),
        ('self.assertRegex(a, b)', 'assert a.search(b)'),
        ('self.assertNotRegex(a, b)', 'assert not a.search(b)'),
    ],
)
def test_rewrite_asserts(before, after):
    assert rewrite_asserts(before) == after


@pytest.mark.parametrize(
    'line', [
        # look like asserts, but aren't
        'self.someFunction()',
        'assertEqual(a, b)',

        # unsupported things
        'self.assertCountEqual(a, b)',
    ],
)
def test_doesnt_rewrite_asserts(line):
    assert rewrite_asserts(line) == line
