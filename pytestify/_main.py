import argparse
from pathlib import Path
from typing import Optional, Sequence

from pytestify.fixes.asserts import rewrite_asserts
from pytestify.fixes.base_class import remove_base_class
from pytestify.fixes.method_name import rewrite_method_name


def _fix_file(filename: str, args: argparse.Namespace) -> int:
    path = Path(filename)
    if not path.is_file():
        raise ValueError(f"File: '{filename}' does not exist")

    orig_contents = path.read_text()

    # apply fixes
    contents = remove_base_class(orig_contents)
    contents = rewrite_method_name(contents)
    contents = rewrite_asserts(contents)

    # return 1 if any fixes were made, otherwise 0
    return int(contents == orig_contents)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    ret = 0
    for filename in args.filenames:
        ret |= _fix_file(filename, args)
    return ret


if __name__ == '__main__':
    exit(main())
