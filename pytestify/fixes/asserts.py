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
        if not hasattr(call.func, 'attr'):
            # this occurs when the method is not called from 'self' --
            # we should skip these occurrences
            continue
        method = call.func.attr
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


def rewrite_asserts(contents: str) -> str:
    tokens = src_to_tokens(contents)
    asserts = get_asserts(contents, tokens)
    content_list = contents.splitlines()
    for _assert in asserts:
        offset = 0
        assert_type = ASSERT_TYPES[_assert.name]
        tokens_after = [
            tok for i, tok in enumerate(
                tokens,
            ) if i > _assert.token_idx
        ]

        # if one line, strip parentheses
        if _assert.line_length == 1:
            open_paren = next(
                t for t in tokens_after if t.name == 'OP' and t.src == '('
            )
            close_paren = next(
                t for t in tokens_after if t.name == 'OP' and t.src == ')'
            )

            line = content_list[_assert.line]
            for token in [close_paren, open_paren]:
                line = remove_token(line, token)

            offset -= 1  # removing the open paren offsets the line by one
            content_list[_assert.line] = line

        # for equality comparators, turn the next comma into ' ==', etc
        if assert_type.type == 'binary':
            operator = assert_type.op
            strip = assert_type.strip

            comma = next(
                t for t in tokens_after if t.name ==
                'OP' and t.src == ','
            )
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
