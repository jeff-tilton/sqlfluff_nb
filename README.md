# sqlfluff_nb
## A SQL linter for notebooks

**sqlfluff_nb** is a wrapper around [sqlfluff](https://github.com/sqlfluff/sqlfluff).  It can be used as a command line tool or as a pre-commit hook.

## Installation 
pip install git+https://github.com/jeff-tilton/sqlfluff_nb

## Usage

**sqlfluff_nb** has implemented [sqlfluff](https://github.com/sqlfluff/sqlfluff)'s fix api command currently.

### Command line

`sfnb path/to/file.ipynb --dialect tsql --config_path path/to/.sqlfluff`

### pre-commit

```
repos:
    -   repo: https://github.com/jeff-tilton/sqlfluff_nb
        rev: v0.1.2-alpha
        hooks:
        -   id: sqlfluff-nb-fix
            name: sqlfluff-nb-fix
            files: \.ipynb$
            entry: sfnb --dialect tsql --config_path ./.sqlfluff
            description: 'Fixes sql lint errors with `SQLFluff`'
            require_serial: true
            additional_dependencies: []
```