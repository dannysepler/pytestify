import argparse
from pathlib import Path
from typing import Optional, Sequence, Union

from pytestify.fixes.asserts import rewrite_asserts
from pytestify.fixes.base_class import remove_base_class
from pytestify.fixes.method_name import rewrite_method_name
from pytestify.fixes.raises import rewrite_raises


def _no_ws(s: str) -> str:
    """ strip all whitespace from a string """
    return ''.join(s.split())


def _fix_path(filepath: Union[str, Path], args: argparse.Namespace) -> int:
    path = Path(filepath)
    if not path.exists():
        ValueError(f"Path: '{filepath}' does not exist")
    if path.is_dir():
        return sum(_fix_path(f, args) for f in path.glob('**/*.py'))

    orig_contents = path.read_text()

    # apply fixes
    contents = remove_base_class(orig_contents)
    contents = rewrite_method_name(contents)
    contents = rewrite_asserts(contents)
    contents = rewrite_raises(contents)

    changes_made = bool(_no_ws(contents) != _no_ws(orig_contents))
    if changes_made:
        print(f'Fixing {path.resolve()}')
        path.write_text(contents)
    return int(changes_made)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filepaths', nargs='*')
    args = parser.parse_args(argv)

    ret = 0
    for filepath in args.filepaths:
        ret += _fix_path(filepath, args)
    return ret


if __name__ == '__main__':
    exit(main())
