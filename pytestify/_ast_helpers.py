import ast
import warnings
from typing import Any, List, Optional


def ast_parse(contents: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return ast.parse(contents.encode())


def is_valid_syntax(contents: str) -> bool:
    try:
        ast_parse(contents)
    except SyntaxError:
        return False
    return True


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
            'finalbody',  # finally in try / except
        ]
        for container in containers:
            children = getattr(elem, container, [])
            if not isinstance(children, list):
                children = [children]
            queue |= set(children)
    return elems


def imports_pytest_as(contents: str) -> Optional[str]:
    for imp in elems_of_type(contents, ast.Import):
        for alias in imp.names:
            if alias.name == 'pytest':
                return alias.asname or 'pytest'
    return None
