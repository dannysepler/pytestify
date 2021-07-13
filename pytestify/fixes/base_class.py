import ast
from typing import List, NamedTuple, Union

from pytestify._ast_helpers import elems_of_type


class TestClass(NamedTuple):
    name: str
    line: int


def is_test_class(base: Union[ast.Attribute, ast.Name]) -> bool:
    if isinstance(base, ast.Attribute):
        # looks like 'class MyClass(a.b):'
        base_id = getattr(base.value, 'id', None)
        return base_id == 'unittest' and base.attr == 'TestCase'
    else:
        # looks like 'class MyClass(a):'
        return getattr(base, 'id', None) == 'TestCase'


def get_test_classes(contents: str) -> List[TestClass]:
    test_classes = []
    for elem in elems_of_type(contents, ast.ClassDef):
        if any(is_test_class(base) for base in elem.bases):
            line = elem.lineno - 1
            test_classes.append(TestClass(elem.name, line))
    return test_classes


def remove_base_class(contents: str) -> str:
    test_classes = get_test_classes(contents)
    content_list = contents.splitlines()

    # todo: detect if unittest has been aliased as something else
    variations = [
        'unittest.TestCase, ',
        'unittest.TestCase',
        'TestCase, ',
        'TestCase',
    ]
    for test_cls in test_classes:
        cls_name = test_cls.name
        i = test_cls.line
        line = content_list[i]
        for variation in variations:
            line = line.replace(variation, '')

        # delete empty paren if they exist
        line = line.replace(f'{cls_name}():', f'{cls_name}:')

        # prefix with "test" if not already. Strip out 'Tests' or 'Test'
        # from the name if either is there
        if not test_cls.name.startswith('Test'):
            if 'Tests' in cls_name:
                cls_name = cls_name.replace('Tests', '')
            elif 'Test' in cls_name:
                cls_name = cls_name.replace('Test', '')
            cls_name = 'Test' + cls_name
            line = line.replace(test_cls.name, cls_name)

        content_list[i] = line

    contents = '\n'.join(content_list)
    return contents
