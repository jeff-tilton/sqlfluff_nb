import json
import logging

import sqlfluff
import typer

LOGGER = logging.getLogger(__name__)


def read_nb(filename: str) -> dict:
    """Reads Notebook as json string returns dict"""
    with open(filename) as f:
        nb = json.loads(f.read())
    return nb


def get_cells(nb: dict) -> list:
    try:
        cells = nb["cells"]
    except KeyError as e:
        LOGGER.error("Notebook does not contain cells")
        raise KeyError() from e
    return cells


def cell_is_code(cell: dict) -> bool:
    try:
        cell_type = cell["cell_type"]
    except KeyError as e:
        LOGGER.info("Cell does not contain type")
        return False
    return cell_type == "code"


def language_is_sql(cell: dict) -> bool:
    try:
        metadata = cell["metadata"]
    except KeyError as e:
        LOGGER.info("Cell does not contain metadata")
        return False
    language = metadata.get("language")
    return language == "sql"


def get_source(cell: dict) -> list:
    try:
        source = cell["source"]
    except KeyError as e:
        LOGGER.info("Cell does not contain source")
        raise KeyError from e
    return source


def fix_sql(source: list, **kwargs) -> str:
    current_source = " ".join(source).replace("\r", " ")
    try:
        new_source = sqlfluff.fix(current_source, **kwargs)
    except Exception as e:
        LOGGER.error(f"Error fixing {current_source}", exc_info=True)
        raise e
    return new_source


def fix_nb(nb: dict, **kwargs) -> dict:
    cells = get_cells(nb)
    for cell in cells:
        if cell_is_code(cell) and language_is_sql(cell):
            try:
                source = get_source(cell)
            except Exception as e:
                LOGGER.warning("Could not get source")
                continue
            try:
                source = fix_sql(source, **kwargs)
            except Exception as e:
                LOGGER.warning("Could not fix source")

            cell["source"] = source
    return nb


def get_kwargs(ctx: typer.Context) -> dict:
    l = ctx.args
    kwargs = {}
    for t in zip(l, l[1:]):
        kwargs.update({t[0].replace("-", ""): t[1]})
    return kwargs


app = typer.Typer()


@app.callback()
def callback():
    """
    SQLFluff wrapper for Notebooks
    """


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def fix(filename: str, ctx: typer.Context):
    current_nb = read_nb(filename)
    kwargs = get_kwargs(ctx)
    new_nb = fix_nb(current_nb, **kwargs)
    if current_nb == new_nb:
        return 0
    nb_string = json.dumps(new_nb, indent=4)
    with open(filename, "w", encoding="UTF-8") as f:
        f.write(nb_string)
    return 1


if __name__ == "__main__":
    SystemExit(app())
