import click
from .iam import iam

@click.group()
def cli():
    """CLI to interact with ebrains services."""
    pass

cli.add_command(iam, "iam")

from .bucket import bucket
cli.add_command(bucket, "bucket")
