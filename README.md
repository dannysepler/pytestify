pytestify
=========

[![alt](http://img.shields.io/pypi/v/pytestify.svg)](https://pypi.python.org/pypi/pytestify)
[![alt](https://img.shields.io/conda/vn/conda-forge/pytestify.svg)](https://anaconda.org/conda-forge/pytestify)

A tool to automatically change unittest to pytest. Similar to
[unittest2pytest](https://github.com/pytest-dev/unittest2pytest),
but with a few more features and written using AST and tokenize, rather
than lib2to3.

Big thanks to [pyupgrade](https://github.com/asottile/pyupgrade/), which
this project has learned from.

## Installation

`pip install pytestify`

## Usage

`pytestify path/to/file.py`

or

`pytestify path/to/folder/`

**Optional arguments**

- [--keep-method-casing](#camelCase-to-snake_case)
- [--keep-count-equal](#assertCountEqual)

Please read over all changes that pytestify makes. It's a new
package, so there are bound to be issues.

## Implemented features

### Test class names

Remove `TestCase` parent class, and make sure tests start with `Test`. We are keeping the test classes themselves, but you can remove them manually.

```python
class TestThing(unittest.TestCase):  # class TestThing:
class TestThing(TestCase, ClassB):   # class TestThing(ClassB):
class ThingTest(unittest.TestCase):  # class TestThing:
class Thing(unittest.TestCase):      # class TestThing:
```

### Setup / teardowns

```python
def setUp(self):          # def setup_method(self):
def tearDown(self):       # def teardown_method(self):
def setUpClass(self):     # def setup_class(self):
def tearDownClass(self):  # def teardown_class(self):
```

### Asserts

Rewrite unittest assert methods using the `assert` keyword.

```python
# asserting one thing
self.assertTrue(a)       # assert a
self.assertFalse (a)     # assert not a
self.assertIsNone(a)     # assert a is None
self.assertIsNotNone(a)  # assert a is not None

# asserting two things
self.assertEqual(a, b)      # assert a == b
self.assertNotEqual(a, b)   # assert a != b
self.assertIs(a, b)         # assert a is b
self.assertIsNot(a, b)      # assert a is not b
self.assertIn(a, b)         # assert a in b
self.assertNotIn(a, b)      # assert a not in b
self.assertListEqual(a, b)  # assert a == b
self.assertDictEqual(a, b)  # assert a == b
self.assertSetEqual(a, b)   # assert a == b
self.assertGreater(a, b)    # assert a > b
self.assertLess(a, b)       # assert a < b
self.assertGreaterEqual(a, b)  # assert a >= b
self.assertLessEqual(a, b)  # assert a <= b
self.assertRegex(a, b)      # assert a.search(b)
self.assertNotRegex(a, b)   # assert not a.search(b)

self.assertAlmostEqual(a, b)
#   assert a == pytest.approx(b)
self.assertAlmostEqual(a, b, places=2)
#   assert a == pytest.approx(b, abs=0.01)
self.assertAlmostEquals(a, b, delta=2)
#   assert a == pytest.approx(b, abs=2)


# improves the assert if reasonable
self.assertEqual(a, None)   # assert a is None
self.assertEqual(a, True)   # assert a is True


# error messages
self.assertTrue(a, msg='oh no!')  # assert a, 'oh no!'
```

### Multi-line asserts

Since `assert (a == b, 'err')`  is equivalent to asserting a tuple, and thus is always `True`.

```python
self.assertEqual(    # assert a == \
    a,               #     b
    b,
)

self.assertEqual(    # assert a == \
    a,               #     b, \
    b,               #     'oh no!'
    msg='oh no!'
)
```


### camelCase to snake_case

Disable this behavior with `--keep-method-casing`

```python
def testThing(self):      # def test_thing(self):
def testHTTPThing(self):  # def test_httpthing(self):
```

### assertCountEqual

Disable this behavior with `pytest path/to/file --keep-count-equal`.

```python
self.assertItemsEqual(a, b)  # assert sorted(a) == sorted(b)
self.assertCountEqual(a, b)  # assert sorted(a) == sorted(b)
```

Note that pytest has no version of either of these methods. See
[this thread](https://github.com/pytest-dev/pytest/issues/5548) for more
information. You can also use
[unittest's implementation](https://stackoverflow.com/a/45946306).

### Exceptions

```python
self.assertRaises(OSError)             # pytest.raises(OSError)
self.assertWarns(OSError)              # pytest.warns(OSError)
with self.assertRaises(OSError) as e:  # with pytest.raises(OSError) as e
with self.assertWarns(OSError) as e:   # with pytest.warns(OSError) as e
```

### Skipping / Expecting failure

```python
# decorated
@unittest.skip('some reason')    # @pytest.mark.skip('some reason')
@unittest.skipIf(some_bool)      # @pytest.mark.skipif(some_bool)
@unittest.skipUnless(some_bool)  # @pytest.mark.skipif(not some_bool)
@unittest.expectedFailure        # @pytest.mark.xfail

# not decorated
unittest.skip('some reason')     # pytest.skip('some reason')
unittest.skipTest('some reason') # pytest.skip('some reason')
unittest.fail('some reason')     # pytest.fail('some reason')
```
