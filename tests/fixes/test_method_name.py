import pytest

from pytestify.fixes.method_name import rewrite_method_name


@pytest.mark.parametrize(
    'before, after', [
        ('def setUpClass(self): pass', 'def setup_class(self): pass'),
        ('def tearDownClass(self): pass', 'def teardown_class(self): pass'),
        ('def setUp(self): pass', 'def setup_method(self): pass'),
        ('def tearDown(self): pass', 'def teardown_method(self): pass'),
        ('def testThing(self): pass', 'def test_thing(self): pass'),
        ('def testHTTPThing(self): pass', 'def test_httpthing(self): pass'),
    ],
)
def test_rewrite_method_name(before, after):
    assert rewrite_method_name(before) == after


@pytest.mark.parametrize(
    'line', [
        'def testThing(self): pass',
        'def testHTTPThing(self): pass',
    ],
)
def test_doesnt_rewrite_if_keeping_casing(line):
    assert rewrite_method_name(line, keep_casing=True) == line


@pytest.mark.parametrize(
    'line', [
        '# def setUp(self): pass',
        'def setup(self): pass',
    ],
)
def test_doesnt_rewrite_method_name(line):
    assert rewrite_method_name(line) == line
