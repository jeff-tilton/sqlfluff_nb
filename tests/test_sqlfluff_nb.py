import json
import os
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from sqlfluff_nb import __version__
from sqlfluff_nb.main import (
    fix_nb,
    fix_sql,
    format_file,
    get_cells,
    get_source,
    language_is_sql,
    read_nb,
)

PATH = Path(__file__).parent


def test_version():
    assert __version__ == "0.1.0"


def test_read_nb():
    assert type(read_nb(os.path.join(PATH, "current_nb.ipynb"))) is dict


def test_get_cells():
    nb = read_nb(os.path.join(PATH, "current_nb.ipynb"))
    assert type(get_cells(nb)) is list


def test_is_language_returns_false_no_meta():
    cell = {}
    assert language_is_sql(cell) is False


def test_is_language_returns_false_no_language():
    cell = {"metadata": {}}
    assert language_is_sql(cell) is False


def test_is_language_returns_false_language_not_sql():
    cell = {"metadata": {"language": "python"}}
    assert language_is_sql(cell) is False


def test_is_language_returns_true_language_sql():
    cell = {"metadata": {"language": "sql"}}
    assert language_is_sql(cell) is True


def test_get_source():
    cell = {"source": ["this is the source"]}
    assert type(get_source(cell)) is list


def test_get_source_raises_error():
    cell = {"not_source": ["this is the source"]}
    with pytest.raises(KeyError):
        get_source(cell)


def test_fix_sql():
    source = [
        "\rselect \ncolumn1, column2 As \rmyname",
        "FROM\nmyschema.atable\n\nSeLEct",
        "*, 1, blah as  fOO  from mySchema.myTable\n\nSelect\n    c as bar,\n",
        "    a + b + c as foo\n\rfrOm myschema.my_table\n",
    ]
    expected_new_source = [
        "\rselect \ncolumn1, column2 As \rmyname",
        "FROM\nmyschema.atable\n\nSeLEct",
        "*, 1, blah as  fOO  from mySchema.myTable\n\nSelect\n    c as bar,\n",
        "    a + b + c as foo\n\rfrOm myschema.my_table\n",
    ]
    assert expected_new_source == fix_sql(source, dialect="tsql")


def test_fix_nb():
    with open(os.path.join(PATH, "current_nb.ipynb")) as f:
        current_nb = json.loads(f.read())

    with open(os.path.join(PATH, "fixed_nb.ipynb")) as f:
        fixed_nb = json.loads(f.read())
    assert fixed_nb == fix_nb(deepcopy(current_nb))


def test_format_file_equal_source():
    assert format_file(os.path.join(PATH, "fixed_nb.ipynb")) == 0


def test_format_file_equal_source():
    shutil.copyfile(
        os.path.join(PATH, "current_nb.ipynb"),
        os.path.join(PATH, "current_nb_copy.ipynb"),
    )
    assert format_file(os.path.join(PATH, "current_nb_copy.ipynb")) == 1

    with open(os.path.join(PATH, "current_nb_copy.ipynb")) as f:
        current_nb = json.loads(f.read())

    with open(os.path.join(PATH, "fixed_nb.ipynb")) as f:
        fixed_nb = json.loads(f.read())

    assert current_nb == fixed_nb
