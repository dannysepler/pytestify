import ast
import warnings
from typing import List


def ast_parse(contents: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents.encode())


def elems_of_type(contents: str, elem_type: ast.stmt) -> List[ast.stmt]:
    module = ast_parse(contents)
    queue = set(module.body)
    elems = []
    while queue:
        elem = queue.pop()
        if isinstance(elem, elem_type):
            elems.append(elem)
        if hasattr(elem, 'body'):
            queue |= set(elem.body)
    return elems
