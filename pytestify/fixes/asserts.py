import ast
import re
from tokenize import TokenError
from typing import List, NamedTuple, Optional

from tokenize_rt import Token, src_to_tokens

from pytestify._ast_helpers import NodeVisitor
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
    'assertAlmostEqual': _Assert(
        'binary',
        op=' == pytest.approx(',
        suffix=')',
        strip=True,
    ),
}

ALIASES = {
    # deprecated name -> current name
    'assertAlmostEquals': 'assertAlmostEqual',
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
        places: Optional[int] = None,
    ):
        self.name = name
        self.line = line
        self.token_idx = token_idx
        self.end_line = end_line
        self.offset = 0
        self.places = places

    @property
    def line_length(self) -> int:
        return (self.end_line - self.line) + 1

    @property
    def rel(self) -> Optional[int]:
        ''' useful for pytest.approx '''
        if self.places is None:
            return None
        return 10 ** (self.places * -1)


class Visitor(NodeVisitor):
    def __init__(self, tokens: List[Token]):
        self.calls: List[Call] = []
        self.tokens = tokens

    def visit_Call(self, call: ast.Call) -> None:
        method = getattr(call.func, 'attr', None)
        if not method or method not in ASSERT_TYPES:
            return

        line = call.lineno
        call_idx = next(
            tok_no for tok_no, tok in enumerate(self.tokens)
            if tok.src == method and tok.line == line
        )

        operators = [
            t for i, t in enumerate(self.tokens)
            if i >= call_idx and t.name == 'OP'
        ]
        open_paren = next(t for t in operators if t.src == '(')
        close_paren = find_closing_paren(open_paren, operators)
        kwargs = {}
        for keyword in call.keywords or []:
            if keyword.arg == 'places':
                # assertAlmostEqual / assertAlmostEquals
                const = keyword.value
                try:
                    kwargs['places'] = const.value  # type: ignore
                except AttributeError:
                    # Prior to Python 3.8, const is actually a ast.Num object
                    kwargs['places'] = const.n  # type: ignore
        end_line = close_paren.line
        self.calls.append(
            Call(method, line - 1, call_idx, end_line - 1, **kwargs),
        )


def rewrite_parens(
    operators: List[Token],
    call: Call,
    content_list: List[str],
    comma: Optional[Token],
) -> bool:
    '''
    For single line asserts, remove parantheses
    For multi-line asserts, convert parantheses to slashes
    '''
    open_paren = next(t for t in operators if t.src == '(')
    closing_paren = find_closing_paren(open_paren, operators)

    start_line = content_list[call.line]
    start_line = remove_token(start_line, open_paren, offset=call.offset)
    content_list[call.line] = start_line

    if call.line_length == 1 or comma and comma.line == open_paren.line:
        call.offset -= 1  # removing the open paren shifts all chars left

    end_line = content_list[call.end_line]
    offset = call.offset if call.line_length == 1 else 0
    end_line = remove_token(
        end_line, closing_paren,
        offset=offset, strip=True,
    )
    if not end_line.strip():
        content_list.pop(call.end_line)
        call.end_line -= 1
        return True
    else:
        content_list[call.end_line] = end_line
        return False


def combine_assert(call: Call, content_list: List[str]) -> bool:
    if content_list[call.line].strip() == 'assert':
        second_line = content_list.pop(call.line + 1)
        content_list[call.line] += second_line.lstrip()
        call.end_line -= 1
        return True
    else:
        return False


def add_slashes(call: Call, content_list: List[str]) -> None:
    contents = '\n'.join(content_list[call.line: call.end_line + 1])
    try:
        tokens = src_to_tokens(contents)
    except TokenError:
        # there's a special character in the line
        tokens = []

    comma = find_outer_comma(tokens, stack_loc=0)
    for i in range(call.line, call.end_line):
        line = content_list[i]

        if line.endswith(',') and comma and comma.line == i - call.line + 1:
            # this is on multiline asserts with an error message
            # otherwise, the comma is probably between elements in a sequence
            pass
        elif line.endswith(('{', '[', '(', ',')):
            continue
        comments = [
            t for t in tokens if t.name ==
            'COMMENT' and t.line == i - call.line + 1
        ]

        if comments:
            loc = comments[0].utf8_byte_offset
            line = line[:loc].rstrip() + ' \\  ' + line[loc:]
        else:
            line += ' \\'
        content_list[i] = line


def remove_msg_param(call: Call, content_list: List[str]) -> None:
    lines_to_check = range(call.line, call.end_line + 1)
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


def should_swap_eq_for_is(
    call: Call,
    tokens: List[Token],
    comma: Token,
) -> bool:
    toks_after = [
        tok for i, tok in enumerate(tokens)
        if i > call.token_idx and
        tok.name not in ('UNIMPORTANT_WS', 'ENDMARKER')
    ]
    l_tokens, r_tokens = [], []
    started_paren = False
    reached_comma = False

    for tok in toks_after:
        if started_paren:
            if not reached_comma and tok == comma:
                reached_comma = True
            elif not reached_comma:
                l_tokens.append(tok)
            else:
                r_tokens.append(tok)
        elif tok.name == 'OP' and tok.src == '(':
            started_paren = True

    if r_tokens and r_tokens[-1].name == 'OP' and r_tokens[-1].src == ')':
        r_tokens = r_tokens[:-1]

    return any(
        len(tokens) == 1 and tokens[0].name == 'NAME'
        and tokens[0].src in ['None', 'True', 'False']
        for tokens in [l_tokens, r_tokens]
    )


def remove_trailing_comma(call: Call, contents: List[str]) -> None:
    last = call.end_line
    if contents[last].endswith(','):
        contents[last] = contents[last][:-1]


def rewrite_asserts(contents: str) -> str:
    tokens = src_to_tokens(contents)
    visitor = Visitor(tokens).visit_text(contents)
    content_list = contents.splitlines()

    line_offset = 0
    for call in visitor.calls:
        call.line -= line_offset
        call.end_line -= line_offset
        assert_type = ASSERT_TYPES[call.name]
        ops_after = [
            tok for i, tok in enumerate(tokens)
            if i > call.token_idx and tok.name == 'OP'
        ]

        comma = find_outer_comma(ops_after)
        deleted_end_line = rewrite_parens(ops_after, call, content_list, comma)
        remove_msg_param(call, content_list)
        remove_trailing_comma(call, content_list)

        # for equality comparators, turn the next comma into ' ==', etc
        if assert_type.type == 'binary':
            operator = assert_type.op
            if (
                operator == ' ==' and
                should_swap_eq_for_is(call, tokens, comma)
            ):
                operator = ' is'

            strip = assert_type.strip

            if comma is None:
                raise ValueError('A comma is expected in binary asserts')

            i = comma.line - 1 - line_offset
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
        if call.places:
            for i in range(call.line, call.end_line + 1):
                if 'places' in content_list[i]:
                    line = content_list[i]
                    line = line.replace(
                        f'places={call.places}', f'abs={call.rel}',
                    )
                    content_list[i] = line

        # if the last line is blank, insert the suffix on the line before
        if not content_list[call.end_line].strip():
            call.end_line -= 1

        suffix = assert_type.suffix
        end_line = content_list[call.end_line]
        end_line += suffix
        content_list[call.end_line] = end_line

        did_combine = combine_assert(call, content_list)
        line_offset += int(did_combine) + int(deleted_end_line)
        add_slashes(call, content_list)

    return '\n'.join(content_list)
