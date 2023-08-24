import typing as t
import click
from click.core import Context, Parameter
from click.shell_completion import CompletionItem

@click.group()
def iam_group():
    pass

from .iam import auth
iam_group.add_command(auth)

@click.group()
def cli():
    pass

cli.add_command(iam_group, "iam")
