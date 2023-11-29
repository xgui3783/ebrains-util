import click
from .auth import auth, get_current_token, TokenDoesNotExistException

@click.group()
def iam():
    """IAM API (login/logout/set token)"""
    pass

iam.add_command(auth)

__all__ = [
    "iam",
    "get_current_token",
    "TokenDoesNotExistException",
]
