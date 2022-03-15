from __future__ import annotations

import argparse
import traceback
from pathlib import Path
from typing import Sequence

from pytestify._ast_helpers import is_valid_syntax
from pytestify.fixes.asserts import rewrite_asserts
from pytestify.fixes.base_class import remove_base_class
from pytestify.fixes.funcs import rewrite_pytest_funcs
from pytestify.fixes.imports import add_pytest_import
from pytestify.fixes.method_name import rewrite_method_name


class RuntimeNotes:
    def __init__(self) -> None:
        self.any_invalid_syntax = False


def _no_ws(s: str) -> str:
    """ strip all whitespace from a string """
    return ''.join(s.split())


def _fix_path(
    filepath: str | Path,
    args: argparse.Namespace,
    notes: RuntimeNotes,
) -> int:
    path = Path(filepath)
    if not path.exists():
        ValueError(f"Path: '{filepath}' does not exist")
    if path.is_dir():
        return sum(_fix_path(f, args, notes) for f in path.glob('**/*.py'))

    orig_contents = path.read_text()
    is_valid = is_valid_syntax(orig_contents)

    # apply fixes
    try:
        # if either of the following two rewrites occur,
        # we can assume it's a test file
        contents = remove_base_class(orig_contents)
        contents = rewrite_asserts(
            contents,
            keep_count_equal=args.keep_count_equal,
        )

        is_unittest_file = _no_ws(contents) != _no_ws(orig_contents)
        if is_unittest_file:
            # the camelCase rewrite is especially risky,
            # only do it if we're sure it's a test file
            contents = rewrite_method_name(
                contents,
                keep_casing=args.keep_method_casing,
            )
        contents = rewrite_pytest_funcs(contents)
        contents = add_pytest_import(contents)

        if not contents.endswith('\n'):
            contents += '\n'

    except SyntaxError:
        reason = 'due to the source file having invalid syntax'
        if is_valid:
            reason = 'because of an issue with pytestify'
        print(f'Skipping {path} {reason}')
        notes.any_invalid_syntax = True
        if args.show_traceback:
            traceback.print_exc()
        return 0

    changes_made = bool(_no_ws(contents) != _no_ws(orig_contents))
    if changes_made:
        print(f'Fixing {path}')
        path.write_text(contents)
    return int(changes_made)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filepaths', nargs='*')
    parser.add_argument('--keep-count-equal', action='store_true')
    parser.add_argument('--show-traceback', action='store_true')
    parser.add_argument('--keep-method-casing', action='store_true')
    args = parser.parse_args(argv)

    notes = RuntimeNotes()
    ret = 0
    for filepath in args.filepaths:
        ret += _fix_path(filepath, args, notes)
    if notes.any_invalid_syntax and not args.show_traceback:
        print(
            '\n(Hint: to show the full traceback, '
            "run again with '--show-traceback')",
        )
    return ret


if __name__ == '__main__':
    exit(main())
