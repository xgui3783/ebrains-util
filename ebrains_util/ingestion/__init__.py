import click

from ebrains_ingestion.workflow_template import ls as wft_ls, show as wft_show
from ebrains_ingestion.workflow import submit

@click.group()
def ing():
    """Ingestion (beta)"""
    pass

@click.command()
@click.argument("name", required=False, type=str)
def ls(name: str = None):
    """Show all ingestion pipelines. If name provided, show detail of one pipeline"""
    if name is None:
        wft_ls()
        return
    wft_show(name=name)

@click.command()
@click.argument("name", required=True, type=str, )# help="Name of ingestion workflow to run")
@click.argument("spec", required=True, type=str, )# help="Path to specification. Use - for stdin. Must be a json file")
def submit(name: str, spec):
    """Submit a workflow"""

    ...

ing.add_command(ls, "ls")
ing.add_command(submit, "submit")