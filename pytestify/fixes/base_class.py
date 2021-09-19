from _ast import expr  # isort: skip
import ast
from typing import Dict

from pytestify._ast_helpers import NodeVisitor


def is_test_class(base: expr) -> bool:
    if isinstance(base, ast.Attribute):
        # looks like 'class MyClass(a.b):'
        base_id = getattr(base.value, 'id', None)
        return base_id == 'unittest' and base.attr == 'TestCase'
    else:
        # looks like 'class MyClass(a):'
        return getattr(base, 'id', None) == 'TestCase'


class Visitor(NodeVisitor):
    def __init__(self) -> None:
        self.test_classes: Dict[int, str] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if any(is_test_class(base) for base in node.bases):
            line = node.lineno - 1
            self.test_classes[line] = node.name


def remove_base_class(contents: str) -> str:
    visitor = Visitor().visit_text(contents)
    content_list = contents.splitlines()

    # todo: detect if unittest has been aliased as something else
    variations = [
        'unittest.TestCase, ',
        'unittest.TestCase',
        'TestCase, ',
        'TestCase',
    ]
    for i, orig_name in visitor.test_classes.items():
        line = content_list[i]
        for variation in variations:
            line = line.replace(variation, '')
            orig_name = orig_name.replace(variation, '')

        # delete empty paren if they exist
        line = line.replace(f'{orig_name}():', f'{orig_name}:')

        # prefix with "test" if not already. Strip out 'Tests' or 'Test'
        # from the name if either is there
        if not orig_name.startswith('Test'):
            cls_name = orig_name
            if 'Tests' in cls_name:
                cls_name = cls_name.replace('Tests', '')
            elif 'Test' in cls_name:
                cls_name = cls_name.replace('Test', '')
            cls_name = 'Test' + cls_name
            line = line.replace(orig_name, cls_name)

        content_list[i] = line

    contents = '\n'.join(content_list)
    return contents
