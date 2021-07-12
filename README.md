pytestify
=========

A tool to automatically change unittest to pytest. Very similar
to https://github.com/pytest-dev/unittest2pytest, but with a few more features and written differently.

## Installation

TODO

## Usage

`python pytestify path/to/file.py`
`python pytestify path/to/folder/`

## Implemented features

### Test class names

```python
class TestThing(unittest.TestCase):  # class TestThing:
class ThingTest(unittest.TestCase):  # class TestThing:
class Thing(unittest.TestCase):      # class TestThing:
```

### Setup / teardowns

```python
def setUp(self):     # def setup_method(self):
def tearDown(self):  # def teardown_method(self):
```

### Asserts

```python
self.assertTrue(a)       # assert a
self.assertFalse (a)     # assert not a
self.assertIsNone(a)     # assert a is None
self.assertIsNotNone(a)  # assert a is not None

self.assertEqual(a, b)      # assert a == b
self.assertNotEqual(a, b)   # assert a != b
self.assertIs(a, b)         # assert a is b
self.assertIsNot(a, b)      # assert a is not b
self.assertIn(a, b)         # assert a in b
self.assertNotIn(a, b)      # assert a not in b
self.assertListEqual(a, b)  # assert a == b
self.assertDictEqual(a, b)  # assert a == b
self.assertSetEqual(a, b)   # assert a == b
self.assertItemsEqual(a, b) # assert sorted(a) == sorted(b)
self.assertGreater(a, b)    # assert a > b
self.assertLess(a, b)       # assert a < b
self.assertGreaterEqual(a, b)  # assert a >= b
self.assertLessEqual(a, b)  # assert a <= b
self.assertRegex(a, b)      # assert a.search(b)
self.assertNotRegex(a, b)   # assert not a.search(b)
```

### Exceptions

```python
# before
self.assertRaises(Exception)
with self.assertRaises(Exception):
    ...
with self.assertRaises(Exception) as e:
    ...

# after
import pytest
pytest.raises(Exception)
with pytest.raises(Exception):
    ...
with pytest.raises(Exception) as e:
    ...
```
