from __future__ import annotations

import pytest

from pytestify.fixes.base_class import remove_base_class


@pytest.mark.parametrize(
    'before, after', [
        ('class Cls(unittest.TestCase): pass', 'class TestCls: pass'),
        ('class Cls(TestCase): pass', 'class TestCls: pass'),
        ('class TestCls(unittest.TestCase): pass', 'class TestCls: pass'),
        ('class TestCls(TestCase): pass', 'class TestCls: pass'),
        ('class ClsTests(TestCase): pass', 'class TestCls: pass'),
        ('class ClsTest(TestCase): pass', 'class TestCls: pass'),
        (
            'class ThingTestCase(unittest.TestCase): pass',
            'class TestThing: pass',
        ),
        ('class ThingTestCase(TestCase): pass', 'class TestThing: pass'),
    ],
)
def test_remove_base_class(before, after):
    imports = (
        'import unittest\n' +
        'from unittest import TestCase\n\n'
    )
    assert remove_base_class(imports + before) == imports + after


@pytest.mark.parametrize(
    'line', [
        '# class Cls(unittest.TestClass):',
        'class Cls: pass',
        'class TestCls: pass',
    ],
)
def test_doesnt_remove_base_class(line):
    assert remove_base_class(line) == line
