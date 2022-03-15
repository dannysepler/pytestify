from __future__ import annotations

from typing import Iterable

from tokenize_rt import Token


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


def operators(tokens: list[Token]) -> Iterable[Token]:
    return (tok for tok in tokens if tok.name == 'OP')


def find_outer_comma(
    tokens: list[Token],
    stack_loc: int = 1,
    # TODO: rather than a 'comma_no' arg, it may be nice if this
    # func returns a list
    comma_no: int = 1,
) -> Token | None:
    stack = 0
    for op in operators(tokens):
        if op.src in ['(', '[', '{']:
            stack += 1
        if op.src in [')', ']', '}']:
            stack -= 1
        if op.src == ',' and stack <= stack_loc:
            comma_no -= 1
            if comma_no == 0:
                return op
    return None


def find_closing_paren(paren: Token, tokens: list[Token]) -> Token:
    found_paren = False
    stack = 1
    for op in operators(tokens):
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
