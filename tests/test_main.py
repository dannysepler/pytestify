import pytest

from pytestify._main import main


@pytest.fixture
def f(tmp_path):
    return tmp_path / 'f.py'


def test_passes_no_change(f):
    f.write_text('1 + 1')
    ret = main([str(f)])
    assert ret == 0


def test_preserves_blank_line(f):
    f.write_text('self.assertEquals(a, b)\n')
    ret = main([str(f)])

    assert f.read_text() == 'assert a == b\n'
    assert ret == 1
