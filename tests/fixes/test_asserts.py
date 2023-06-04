from __future__ import annotations

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
        ('self.assertDictEqual(a, b)', 'assert a == b'),
        ('self.assertListEqual(a, b)', 'assert a == b'),
        ('self.assertSetEqual(a, b)', 'assert a == b'),
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
        ('self.assertIsInstance(a, b)', 'assert isinstance(a, b)'),
        ('self.assertAlmostEquals(a, b)', 'assert a == pytest.approx(b)'),
        (
            'self.assertAlmostEquals(a, b) # hi',
            'assert a == pytest.approx(b) # hi',
        ),
        (
            # The next two cases check the placement of the parenthesis
            'self.assertAlmostEquals(a, b, msg="Error")',
            'assert a == pytest.approx(b), "Error"',
        ),
        (
            'self.assertAlmostEquals(a, b, "Error")',
            'assert a == pytest.approx(b), "Error"',
        ),
        (
            'self.assertAlmostEquals(a, b, places=2)',
            'assert a == pytest.approx(b, abs=0.01)',
        ),
        (
            'self.assertAlmostEquals(a, b, delta=2)',
            'assert a == pytest.approx(b, abs=2)',
        ),
        (
            'self.assertAlmostEquals(a, b, delta=timedelta(minutes=1))',
            # delta as a timedelta isn't supported by pytest yet,
            # just check it doesn't fail
            # https://github.com/pytest-dev/pytest/issues/8395
            'assert a == pytest.approx(b, delta=timedelta(minutes=1))',
        ),
    ],
)
def test_rewrite_simple_asserts(before, after):
    assert rewrite_asserts(before) == after


@pytest.mark.parametrize(
    'before, after', [
        ('self.assertEqual([a, b, c], d)', 'assert [a, b, c] == d'),
        ('self.assertEqual(len(a), len(b))', 'assert len(a) == len(b)'),
        # TODO: failing on CI? Not sure why
        # ('self.assertEqual(1, None)', 'assert 1 is None'),
        # ('self.assertEqual(a, True)', 'assert a is True'),
        # ('self.assertEqual(a, False)', 'assert a is False'),
        (
            'self.assertEqual(a, [True, False, None])',
            'assert a == [True, False, None]',
        ),
        ('self.assertEqual(a, "True")', 'assert a == "True"'),
        (
            'self.assertEqual(min(1, 2, 3), min(1, 2, 3))',
            'assert min(1, 2, 3) == min(1, 2, 3)',
        ),
        (
            'self.assertEqual(min(1, 2, 3), 1)\n'
            'self.assertEqual(1, 1)\n',
            'assert min(1, 2, 3) == 1\n'
            'assert 1 == 1',
        ),
        (
            'try:\n'
            '    pass\n'
            'except SomeException:\n'
            '    self.assertEqual(1, 1)',
            'try:\n'
            '    pass\n'
            'except SomeException:\n'
            '    assert 1 == 1',
        ),
        (
            'if a == b:\n'
            '    pass\n'
            'else:\n'
            '    self.assertEqual(1, 1)',
            'if a == b:\n'
            '    pass\n'
            'else:\n'
            '    assert 1 == 1',
        ),
        (
            'try:\n'
            '    pass\n'
            'except:\n'
            '    pass\n'
            'finally:\n'
            '    self.assertEqual(1, 1)',
            'try:\n'
            '    pass\n'
            'except:\n'
            '    pass\n'
            'finally:\n'
            '    assert 1 == 1',
        ),
        (
            'self.assertIsNone(\n'
            '    a\n'
            ')',
            'assert a is None',
        ),
        (
            'self.assertEqual(\n'
            '    a,\n'
            '    [\n'
            '        1,\n'
            '        2,\n'
            '    ]\n'
            ')',
            'assert a == \\\n'
            '    [\n'
            '        1,\n'
            '        2,\n'
            '    ]',
        ),
        (
            'self.assertEqual(\n'
            '    a,\n'
            '    b,\n'
            ')',
            'assert a == \\\n'
            '    b',
        ),
        (
            'self.assertEqual(\n'
            '    a, b\n'
            ')\n'
            'self.assertEqual(\n'
            '    c, d\n'
            ')',
            'assert a == b\n'
            'assert c == d',
        ),
        (
            'self.assertDictEqual(a, {\n'
            "    'a': 1,\n"
            '})',
            'assert a == {\n'
            "    'a': 1,\n"
            '}',
        ),
        (
            'self.assertIsInstance(x, y)\n'
            'self.assertIsInstance(x, y)',
            'assert isinstance(x, y)\n'
            'assert isinstance(x, y)',
        ),
    ],
)
def test_rewrite_complex_asserts(before, after):
    assert rewrite_asserts(before) == after


@pytest.mark.parametrize(
    'before, after', [
        (
            "self.assertEquals(a, b, msg='Error')",
            "assert a == b, 'Error'",
        ),
        (
            "self.assertEquals(a, b, msg = 'Error')",
            "assert a == b, 'Error'",
        ),
        (
            "self.assertEquals(a, b, msg     =     'Error')",
            "assert a == b, 'Error'",
        ),
        (
            'self.assertEquals(\n'
            '   a,\n'
            '   b,\n'
            "   msg='Error'\n"
            ')',
            'assert a == \\\n'
            '   b, \\\n'
            "   'Error'",
        ),
        (
            '# some comment\n'
            'self.assertEquals(\n'
            '   a,\n'
            '   b,\n'
            "   msg='Error'\n"
            ')',
            '# some comment\n'
            'assert a == \\\n'
            '   b, \\\n'
            "   'Error'",
        ),
        (
            '# some comment\n'
            '# some other comment\n'
            'self.assertEquals(\n'
            '   a,\n'
            '   b,\n'
            "   msg='Error'\n"
            ')',
            '# some comment\n'
            '# some other comment\n'
            'assert a == \\\n'
            '   b, \\\n'
            "   'Error'",
        ),
        (
            'self.assertEquals(\n'
            '   a,  # some comment\n'
            '   b\n'
            ')',
            'assert a == \\  # some comment\n'
            '   b',
        ),
        (
            'self.assertEquals(\n'
            '   a.func(),\n'
            '   b\n'
            ')',
            'assert a.func() == \\\n'
            '   b',
        ),
        (
            'self.assertAlmostEquals(\n'
            '   a,\n'
            '   b,\n'
            '   places=2\n'
            ')',
            'assert a == pytest.approx(\n'
            '   b,\n'
            '   abs=0.01)',
        ),
        (
            'self.assertAlmostEquals(\n'
            '   a,\n'
            '   b,\n'
            '   delta=2\n'
            ')',
            'assert a == pytest.approx(\n'
            '   b,\n'
            '   abs=2)',
        ),
        (
            'self.assertAlmostEquals(\n'
            '   a,\n'
            '   b # hi\n'
            ')',
            'assert a == pytest.approx(\n'
            '   b) # hi',
        ),
        (
            'self.assertEquals(\n'
            '   [\n'
            '       1,\n'
            '   ],\n'
            '   [\n'
            '       1,\n'
            '   ]\n'
            ')',
            'assert [\n'
            '       1,\n'
            '   ] == \\\n'
            '   [\n'
            '       1,\n'
            '   ]',
        ),
    ],
)
def test_remove_msg_param(before, after):
    assert rewrite_asserts(before) == after


@pytest.mark.parametrize(
    'before, with_count_equal, after', [
        # opted-out
        ('self.assertItemsEqual(a, b)', False, 'self.assertItemsEqual(a, b)'),
        ('self.assertCountEqual(a, b)', False, 'self.assertCountEqual(a, b)'),
        (
            'self.assertItemsEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
            False,
            'self.assertItemsEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
        ),
        (
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
            False,
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
        ),
        (
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b,\n'
            '    "some error message"\n'
            ')',
            False,
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b,\n'
            '    "some error message"\n'
            ')',
        ),

        # opted-in
        (
            'self.assertItemsEqual(a, b)',
            True,
            'assert sorted(a) == sorted(b)',
        ),
        (
            'self.assertCountEqual(a, b)',
            True,
            'assert sorted(a) == sorted(b)',
        ),
        (
            'self.assertCountEqual(a, b, "error")', True,
            'assert sorted(a) == sorted(b), "error"',
        ),

        # TODO: better format the following multilines
        (
            'self.assertItemsEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
            True,
            'assert sorted(\n'
            '    a) == sorted(\n'
            '    b)',
        ),
        (
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b\n'
            ')',
            True,
            'assert sorted(\n'
            '    a) == sorted(\n'
            '    b)',
        ),
        (
            'self.assertCountEqual(\n'
            '    a,\n'
            '    b,\n'
            '    msg="Error"\n'
            ')',
            True,
            'assert sorted(\n'
            '    a) == sorted(\n'
            '    b), \\\n'
            '    "Error"',
        ),
    ],
)
def test_opt_in_rewrites(before, with_count_equal, after):
    assert rewrite_asserts(before, with_count_equal=with_count_equal) == after


@pytest.mark.parametrize(
    'line', [
        # look like asserts, but aren't
        'self.someFunction()',
        'assertEqual(a, b)',
    ],
)
def test_doesnt_rewrite_asserts(line):
    assert rewrite_asserts(line) == line
