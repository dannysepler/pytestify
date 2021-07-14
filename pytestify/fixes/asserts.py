import ast
import re
from typing import List, NamedTuple

from tokenize_rt import Token, src_to_tokens

from pytestify._ast_helpers import elems_of_type
from pytestify._token_helpers import (
    find_closing_paren, find_outer_comma, remove_token,
)


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
    'assertDictEqual': _Assert('binary', op=' =='),
    'assertSetEqual': _Assert('binary', op=' =='),
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
    'assertItemsEqual': _Assert(
        'binary',
        prefix='sorted(',
        op=') == sorted(',
        suffix=')',
        strip=True,
    ),
    'assertIsInstance': _Assert(
        'binary',
        prefix='isinstance(',
        op=',',
        suffix=')',
    ),
}

ALIASES = {
    # deprecated name -> current name
    'assertEquals': 'assertEqual',
    'assertNotEquals': 'assertNotEqual',
}

for alias, orig in ALIASES.items():
    ASSERT_TYPES[alias] = ASSERT_TYPES[orig]


class Call:
    def __init__(
        self,
        name: str,
        line: int,
        token_idx: int,
        end_line: int,
    ):
        self.name = name
        self.line = line
        self.token_idx = token_idx
        self.end_line = end_line
        self.offset = 0

    @property
    def line_length(self) -> int:
        return (self.end_line - self.line) + 1


def get_calls(contents: str, tokens: List[Token]) -> List[Call]:
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
        call_idx = next(
            line_no for line_no, tok in enumerate(tokens)
            if tok.src == method and tok.line == line
        )

        operators = [
            t for i, t in enumerate(
                tokens,
            ) if i >= call_idx and t.name == 'OP'
        ]
        open_paren = next(t for t in operators if t.src == '(')
        close_paren = find_closing_paren(open_paren, operators)
        end_line = close_paren.line
        calls.append(Call(method, line - 1, call_idx, end_line - 1))
    return calls


def rewrite_parens(
    operators: List[Token],
    call: Call,
    content_list: List[str],
) -> None:
    '''
    For single line asserts, remove parantheses
    For multi-line asserts, convert parantheses to slashes
    '''
    open_paren = next(t for t in operators if t.src == '(')
    closing_paren = find_closing_paren(open_paren, operators)

    start_line = content_list[call.line]
    start_line = remove_token(start_line, open_paren, offset=call.offset)
    content_list[call.line] = start_line

    if call.line_length == 1:
        call.offset -= 1  # removing the open paren shifts all chars left

    end_line = content_list[call.end_line]
    end_line = remove_token(
        end_line, closing_paren,
        offset=call.offset, strip=True,
    )
    content_list[call.end_line] = end_line

    last_assert_line = content_list[call.end_line]
    for i in range(call.line, call.end_line):
        line = content_list[i]

        # skip the assertion line as it will add its own space
        if i > call.line:
            line += ' '

        # add trailing slash to all lines except the last with content
        if i < call.end_line - 1:
            line += '\\'
        elif last_assert_line.strip():
            line += '\\'
        else:
            line = line.rstrip()
        content_list[i] = line


def remove_msg_param(call: Call, content_list: List[str]) -> None:
    lines_to_check = range(call.line, call.end_line) or [call.line]
    for line_no in lines_to_check:
        line = content_list[line_no]
        if 'msg' not in line:
            continue

        line = re.sub(r'msg\s*=\s*', '', line)
        if line.endswith('\\'):
            line = line[:-1]
        line = line.rstrip()
        if line.endswith(','):
            line = line[:-1]
        content_list[line_no] = line


def remove_trailing_comma(call: Call, contents: List[str]) -> None:
    last = call.end_line
    penultimate = call.end_line - 1
    if not contents[last].strip() and contents[penultimate].endswith(','):
        contents[penultimate] = contents[penultimate][:-1]


def rewrite_asserts(contents: str) -> str:
    tokens = src_to_tokens(contents)
    calls = get_calls(contents, tokens)
    content_list = contents.splitlines()
    for call in calls:
        assert_type = ASSERT_TYPES[call.name]
        ops_after = [
            tok for i, tok in enumerate(tokens)
            if i > call.token_idx and tok.name == 'OP'
        ]

        rewrite_parens(ops_after, call, content_list)
        remove_msg_param(call, content_list)
        remove_trailing_comma(call, content_list)

        # for equality comparators, turn the next comma into ' ==', etc
        if assert_type.type == 'binary':
            operator = assert_type.op
            strip = assert_type.strip

            comma = find_outer_comma(ops_after)
            i = comma.line - 1
            line = content_list[i]
            line = remove_token(
                line,
                comma,
                replace_with=operator,
                offset=call.offset,
                strip=strip,
            )
            content_list[i] = line

        line = content_list[call.line]
        prefix = assert_type.prefix
        line = line.replace(f'self.{call.name}', f'assert {prefix}')
        content_list[call.line] = line

        # if the last line is blank, insert the suffix on the line before
        if not content_list[call.end_line].strip():
            call.end_line -= 1

        suffix = assert_type.suffix
        end_line = content_list[call.end_line]
        end_line += suffix
        content_list[call.end_line] = end_line

    return '\n'.join(content_list)
