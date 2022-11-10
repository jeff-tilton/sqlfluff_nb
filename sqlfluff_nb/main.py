import json

import typer

from .utils import fix_nb, get_kwargs, read_nb

app = typer.Typer()


@app.callback()
def callback():
    """
    SQLFluff wrapper for Notebooks
    """


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def fix(path: str, ctx: typer.Context):
    current_nb = read_nb(path)
    kwargs = get_kwargs(ctx)
    new_nb = fix_nb(current_nb, **kwargs)
    nb_string = json.dumps(new_nb, indent=4)
    with open(path, "w") as f:
        f.write(nb_string)
