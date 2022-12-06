import argparse
import json
import logging
import logging.config
import sys
from copy import deepcopy
from typing import Sequence
from unittest import TestCase

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
        LOGGER.error("Notebook does not contain cells", exc_info=True)
        raise KeyError() from e
    return cells


def cell_is_code(cell: dict) -> bool:
    try:
        cell_type = cell["cell_type"]
    except KeyError as e:
        LOGGER.debug("Cell does not contain type")
        return False
    return cell_type == "code"


def language_is_sql(cell: dict) -> bool:
    try:
        metadata = cell["metadata"]
    except KeyError as e:
        LOGGER.debug("Cell does not contain metadata")
        return False
    language = metadata.get("language")
    return language == "sql"


def get_source(cell: dict) -> list:
    try:
        source = cell["source"]
    except KeyError as e:
        LOGGER.debug("Cell does not contain source")
        raise KeyError from e
    return source


def fix_sql(current_source: list, **kwargs) -> str:
    if isinstance(current_source, list):
        current_source_joined = "".join(current_source)
    try:
        fixed_source = sqlfluff.fix(current_source_joined, **kwargs)
        LOGGER.debug(f"current_source_joined: {current_source_joined}")
        LOGGER.debug(f"fixed_source: {fixed_source}")
        if current_source_joined != fixed_source:
            LOGGER.info(f"Sources not equal")
            source = []
            fixed_source_split = fixed_source.split("\n")
            for i, v in enumerate(fixed_source_split):
                if i != len(fixed_source_split) - 1:
                    v += "\n"
                else:
                    v = v.rstrip()
                source.append(v.rstrip(" "))
            LOGGER.debug(f"{source}")
        else:
            LOGGER.info(f"Sources equal")
            source = current_source
    except Exception as e:
        LOGGER.error(f"Error fixing {current_source}", exc_info=True)
        raise e

    return source


def fix_nb(nb: dict, **kwargs) -> dict:
    cells = get_cells(nb)
    for cell in cells:
        if cell_is_code(cell) and language_is_sql(cell):
            try:
                current_source = get_source(cell)
                LOGGER.debug(f"{current_source}")
            except Exception as e:
                LOGGER.warning("Could not get source")
                continue
            try:
                source = fix_sql(current_source, **kwargs)
            except Exception as e:
                LOGGER.error("Could not fix source", exc_info=True)
                continue
            cell["source"] = source
    return nb


def format_file(filename: str, **kwargs) -> int:
    current_nb = read_nb(filename)
    new_nb = fix_nb(deepcopy(current_nb), **kwargs)
    try:
        TestCase().assertDictEqual(current_nb, new_nb)
    except AssertionError:
        LOGGER.info(f"Source did not match")
        nb_string = json.dumps(new_nb, indent=2)
        with open(filename, "w", encoding="UTF-8") as f:
            f.write(nb_string)
            LOGGER.info(f"Writing changes to {filename}")
        return 1
    LOGGER.info(f"{filename} did not change")
    return 0


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--dialect", default="ansi")
    parser.add_argument("--level", default=20, type=int)
    parser.add_argument("--rules", default=None, nargs="*")
    parser.add_argument("--exclude_rules", default=None, nargs="*")
    parser.add_argument("--config_path", default=None)
    args = parser.parse_args(argv)
    logging.basicConfig(stream=sys.stderr, level=args.level, format=FORMAT)
    kwargs = {k: v for k, v in vars(args).items() if k not in ["filenames", "level"]}
    retv = 0
    for filename in args.filenames:
        retv |= format_file(filename, **kwargs)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
