import ast
import warnings
from typing import Any, List


def ast_parse(contents: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents.encode())


def elems_of_type(contents: str, elem_type: Any) -> List[Any]:
    module = ast_parse(contents)
    queue = {module}
    elems = []
    while queue:
        elem = queue.pop()
        if isinstance(elem, elem_type):
            elems.append(elem)

        # each of these may have child blocks of code
        containers = [
            'body',  # class or function body
            'handlers',  # exceptions
            'orelse',  # else statements
            'items',  # with statement
            'context_expr',  # context manager
        ]
        for container in containers:
            children = getattr(elem, container, [])
            if not isinstance(children, list):
                children = [children]
            queue |= set(children)
    return elems
