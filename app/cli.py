import os

import click
from flask import Blueprint


bp = Blueprint("cli", __name__, cli_group=None)

CMD_EXTRACT = "pybabel extract -F babel.cfg -k _l -o messages.pot ."
# CMD_EXTRACT = "pybabel extract -F babel.cfg -o messages.pot ."


@bp.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language."""
    if os.system(CMD_EXTRACT):
        raise RuntimeError("Extract command failed.")
    if os.system(f"pybabel init -i messages.pot -d app/translations -l {lang}"):
        raise RuntimeError("Init command failed.")
    os.remove("messages.pot")


@translate.command()
def update():
    """Update all languages."""
    if os.system(CMD_EXTRACT):
        raise RuntimeError("Extract command failed.")
    if os.system("pybabel update -i messages.pot -d app/translations"):
        raise RuntimeError("Update command failed.")
    os.remove("messages.pot")


@translate.command()
def compile():
    """Compile all languages."""
    if os.system("pybabel compile -d app/translations"):
        raise RuntimeError("Compile command failed.")
