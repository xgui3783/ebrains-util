import click

@click.group()
def iam_group():
    pass

from .iam import auth
iam_group.add_command(auth)

@click.group()
def cli():
    pass

cli.add_command(iam_group, "iam")

from .dataproxy import bucket
cli.add_command(bucket, "bucket")
