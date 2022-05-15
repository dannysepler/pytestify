from __future__ import annotations

import pytest

from pytestify._main import main


@pytest.fixture
def f(tmp_path):
    return tmp_path / 'f.py'


def test_passes_no_change(f):
    f.write_text('1 + 1')
    ret = main([str(f)])
    assert ret == 0


def test_preserves_blank_line(f):
    f.write_text('self.assertEquals(a, b)\n')
    ret = main([str(f)])

    assert f.read_text() == 'assert a == b\n'
    assert ret == 1


def test_rewrite_method_names_in_test_file(f):
    f.write_text('''
class TestThing(unittest.TestCase):
    def testCamelCase(self):
        self.assertEqual(1, 2)
''')
    ret = main([str(f)])

    assert f.read_text() == '''
class TestThing:
    def test_camel_case(self):
        assert 1 == 2
'''
    assert ret == 1


def test_doesnt_rewrite_method_names_in_non_test_file(f):
    orig_contents = '''
def camelCaseButNotTest():
    print("don't rewrite me")
'''
    f.write_text(orig_contents)

    ret = main([str(f)])

    assert f.read_text() == orig_contents
    assert ret == 0


class TestCliArgs:
    def test_rewrites_count_equal(self, f):
        f.write_text('self.assertCountEqual(a, b)\n')
        ret = main([str(f), '--with-count-equal'])

        assert f.read_text() == 'assert sorted(a) == sorted(b)\n'
        assert ret == 1

    def test_doesnt_rewrite_count_equal(self, f):
        f.write_text('self.assertCountEqual(a, b)\n')
        ret = main([str(f)])

        assert f.read_text() == 'self.assertCountEqual(a, b)\n'
        assert ret == 0
