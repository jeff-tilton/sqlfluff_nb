import argparse
import json
import logging
import logging.config
from copy import deepcopy
from typing import Sequence

import sqlfluff

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
    }
)
LOGGER = logging.getLogger(__name__)
FORMAT = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"


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
    # LOGGER.info(f"{current_source}")
    try:
        new_source = sqlfluff.fix(current_source, **kwargs)
        LOGGER.info(f"{new_source}")
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
                LOGGER.debug(f"{source}")
            except Exception as e:
                LOGGER.warning("Could not get source")
                continue
            try:
                source = fix_sql(source, **kwargs)
            except Exception as e:
                LOGGER.warning("Could not fix source")

            cell["source"] = source
    return nb


def format_file(filename: str, **kwargs) -> int:
    current_nb = read_nb(filename)
    new_nb = fix_nb(deepcopy(current_nb), **kwargs)

    if current_nb == new_nb:
        LOGGER.info(f"{filename} did not change")
        return 0
    nb_string = json.dumps(new_nb, indent=4)
    with open(filename, "w", encoding="UTF-8") as f:
        f.write(nb_string)
        LOGGER.info(f"Writing changes to {filename}")
    return 1


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--dialect", default="ansi")
    parser.add_argument("--rules", default=None, nargs="*")
    parser.add_argument("--exclude_rules", default=None, nargs="*")
    parser.add_argument("--config_path", default=None)
    args = parser.parse_args(argv)
    kwargs = {k: v for k, v in vars(args).items() if k != "filenames"}
    retv = 0
    for filename in args.filenames:
        retv |= format_file(filename, **kwargs)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
