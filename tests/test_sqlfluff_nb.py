import pytest

from sqlfluff_nb import __version__
from sqlfluff_nb.main import fix_sql, get_cells, get_source, language_is_sql, read_nb

PATH = r"./test.ipynb"


def test_version():
    assert __version__ == "0.1.0"


def test_read_nb():
    assert type(read_nb(PATH)) is dict


def test_get_cells():
    nb = read_nb(PATH)
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
    expected_new_source = "select\n    column1,\n    column2 as myname\nfrom\n    myschema.atable\n\nselect\n    *,\n    1,\n    blah as foo\nfrom myschema.mytable\n\nselect\n    c as bar,\n    a + b + c as foo\nfrom myschema.my_table\n"
    assert expected_new_source == fix_sql(source, dialect="tsql")
