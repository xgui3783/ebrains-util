import sys
from io import BytesIO
import json

import click
from ebrains_ingestion.workflow_template import ls as wft_ls, show as wft_show
from ebrains_ingestion.workflow import submit as wft_submit

from ..iam import get_current_token

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
@click.argument("name", required=True, type=str, )
@click.argument("spec", required=True, type=str, )
def submit(name: str, spec: str):
    """Submit a workflow"""
    token = get_current_token()

    if spec == "-":
        print("Reading stdin for spec", file=sys.stderr)
        spec_str = sys.stdin.buffer.read()
        spec_dict = json.loads(spec_str)
    else:
        with open(spec, "rb") as fp:
            spec_dict = json.load(fp=fp)    


    print(f"submitting {name=}, {spec_dict=}", file=sys.stderr)
    wft_submit(name, track_provenance=False, token=token.token, **spec_dict)
    print("Submission successful")


ing.add_command(ls, "ls")
ing.add_command(submit, "submit")