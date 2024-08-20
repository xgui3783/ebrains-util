import click

from ebrains_iam.collabs import get_collab
from .auth import get_current_token


@click.group()
def admin():
    """Everything admin related (adding user/remove user etc) n.b. token need admin role"""
    pass


ROLE_HELPER_TEXT = r"Role {administrator, editor, viewer}. Default to viewer"
NEEDED_SCOPES = ("clb.wiki.read", "clb.wiki.write")


@click.command()
@click.option("--role", help=ROLE_HELPER_TEXT, default="viewer")
@click.argument("user_id", required=True, type=str)
@click.argument("collab_id", required=True, type=str)
def add_team(role: str, user_id: str, collab_id: str):
    """Add user to a group. Prepend 'service-account-' for service accounts."""
    token = get_current_token()
    assert all(
        scope in token.scope for scope in NEEDED_SCOPES
    ), f"Both {NEEDED_SCOPES} are needed for admin. You current token scopes: {token.scope}"
    collab = get_collab(collab_id=collab_id, token=token.token)
    collab.add_team(user_id, role, token=token.token)


admin.add_command(add_team, "add-team")


@click.command()
@click.option("--role", help=ROLE_HELPER_TEXT, default="viewer")
@click.argument("user_id", required=True, type=str)
@click.argument("collab_id", required=True, type=str)
def remove_team(role: str, user_id: str, collab_id: str):
    """Remove user from a group. Prepend 'service-account-' for service accounts."""
    token = get_current_token()
    assert all(
        scope in token.scope for scope in NEEDED_SCOPES
    ), f"Both {NEEDED_SCOPES} are needed for admin. You current token scopes: {token.scope}"
    collab = get_collab(collab_id=collab_id, token=token.token)
    collab.remove_team(user_id, role, token=token.token)


admin.add_command(remove_team, "remove-team")
