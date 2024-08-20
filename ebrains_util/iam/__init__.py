import click
from .auth import auth, get_current_token, TokenDoesNotExistException
from .admin import admin

@click.group()
def iam():
    """IAM API (login/logout/set token)"""
    pass

iam.add_command(auth)
iam.add_command(admin)

__all__ = [
    "iam",
    "get_current_token",
    "TokenDoesNotExistException",
]
