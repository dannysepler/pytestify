import ast
from typing import List, NamedTuple

from tokenize_rt import Token, src_to_tokens

from pytestify._ast_helpers import elems_of_type


class _Assert(NamedTuple):
    type: str
    prefix: str = ''
    suffix: str = ''
    op: str = ''
    strip: bool = False


# https://docs.python.org/3/library/unittest.html#assert-methods
ASSERT_TYPES = {
    # unary asserts
    'assertTrue': _Assert('unary'),
    'assertFalse': _Assert('unary', prefix='not '),
    'assertIsNone': _Assert('unary', suffix=' is None'),
    'assertIsNotNone': _Assert('unary', suffix=' is not None'),

    # binary asserts
    'assertEqual': _Assert('binary', op=' =='),
    'assertNotEqual': _Assert('binary', op=' !='),
    'assertIs': _Assert('binary', op=' is'),
    'assertIsNot': _Assert('binary', op=' is not'),
    'assertIn': _Assert('binary', op=' in'),
    'assertNotIn': _Assert('binary', op=' not in'),
    'assertListEqual': _Assert('binary', op=' =='),
    'assertGreater': _Assert('binary', op=' >'),
    'assertLess': _Assert('binary', op=' <'),
    'assertGreaterEqual': _Assert('binary', op=' >='),
    'assertLessEqual': _Assert('binary', op=' <='),
    'assertRegex': _Assert('binary', op='.search(', suffix=')', strip=True),
    'assertNotRegex': _Assert(
        'binary',
        prefix='not ',
        op='.search(',
        suffix=')',
        strip=True,
    ),
}

ALIASES = {
    # deprecated name -> current name
    'assertEquals': 'assertEqual',
    'assertNotEquals': 'assertNotEqual',
}

for alias, orig in ALIASES.items():
    ASSERT_TYPES[alias] = ASSERT_TYPES[orig]


class Call(NamedTuple):
    name: str
    line: int
    token_idx: int
    close_paren_line: int

    @property
    def line_length(self) -> int:
        return self.close_paren_line - self.line


def get_asserts(contents: str, tokens: List[Token]) -> List[Call]:
    calls = []
    for expr in elems_of_type(contents, ast.Expr):
        call = expr.value
        if not isinstance(call, ast.Call):
            continue
        method = getattr(call.func, 'attr', None)
        if not method:
            # this occurs when the method is not called from 'self' --
            # we should skip these occurrences
            continue
        if method not in ASSERT_TYPES:
            continue

        line = call.lineno
        token_idx = next(
            line_no for line_no, tok in enumerate(tokens)
            if tok.src == method and tok.line == line
        )
        close_paren_line = next(
            tok.line for tok in tokens
            if tok.name == 'OP' and tok.src == ')'
            and tok.line >= line
        )
        calls.append(Call(method, line - 1, token_idx, close_paren_line))
    return calls


def remove_token(
    line: str,
    token: Token,
    replace_with: str = '',
    offset: int = 0,
    strip: bool = False,
) -> str:
    loc = token.utf8_byte_offset + offset
    before = line[:loc]
    after = line[loc+1:]
    if strip:
        before = before.rstrip(' ')
        after = after.lstrip(' ')
    return before + replace_with + after


def find_outer_comma(operators: List[Token]) -> Token:
    stack = 0
    for op in operators:
        if op.src == '(':
            stack += 1
        if op.src == ')':
            stack -= 1
        if op.src == ',' and stack in (0, 1):
            return op
    raise ValueError('No outer comma found')


def find_closing_paren(paren: Token, operators: List[Token]) -> Token:
    found_paren = False
    stack = 1
    for op in operators:
        if op == paren:
            found_paren = True
            continue
        if found_paren and op.src == '(':
            stack += 1
        if found_paren and op.src == ')':
            stack -= 1
            if stack == 0:
                return op
    raise ValueError('No closing parenthesis was found')


def rewrite_asserts(contents: str) -> str:
    tokens = src_to_tokens(contents)
    asserts = get_asserts(contents, tokens)
    content_list = contents.splitlines()
    for _assert in asserts:
        offset = 0
        assert_type = ASSERT_TYPES[_assert.name]
        ops_after = [
            tok for i, tok in enumerate(tokens)
            if i > _assert.token_idx and tok.name == 'OP'
        ]
        # print(ops_after)

        # if one line, strip the outer parentheses
        if _assert.line_length == 1:
            open_paren = next(t for t in ops_after if t.src == '(')
            closing_paren = find_closing_paren(open_paren, ops_after)

            line = content_list[_assert.line]
            line = remove_token(line, open_paren, offset=offset)
            offset -= 1  # removing the open paren shifts all chars left
            line = remove_token(line, closing_paren, offset=offset)
            content_list[_assert.line] = line

        # for equality comparators, turn the next comma into ' ==', etc
        if assert_type.type == 'binary':
            operator = assert_type.op
            strip = assert_type.strip

            comma = find_outer_comma(ops_after)
            i = comma.line - 1
            line = content_list[i]
            line = remove_token(
                line, comma, replace_with=operator, offset=offset, strip=strip,
            )
            content_list[i] = line

        i = _assert.line
        line = content_list[i]

        prefix = assert_type.prefix
        suffix = assert_type.suffix

        line = line.replace(f'self.{_assert.name}', f'assert {prefix}')
        line += suffix
        content_list[i] = line

    return '\n'.join(content_list)
