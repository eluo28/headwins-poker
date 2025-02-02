import subprocess
from typing import Annotated

import typer

app = typer.Typer()


def call(command: str, env: dict[str, str] | None = None) -> None:
    code = subprocess.call(command, shell=True, env=env)
    if code != 0:
        raise typer.Exit(code)


@app.command()
def fmt() -> None:
    call("poetry run ruff format")


@app.command()
def test(test_name: Annotated[str | None, typer.Argument()] = None) -> None:
    if test_name:
        call(f"poetry run pytest -k {test_name}")
    else:
        call("poetry run pytest")


@app.command()
def fix() -> None:
    call("poetry run ruff check --fix")


@app.command()
def fixall() -> None:
    fmt()
    fix()


if __name__ == "__main__":
    app()
