from ebrains_iam.device_flow import start as start_device_flow
from ebrains_iam.client_credential import ClientCredentialsSession
from .config import token_path
import json
import click
import base64
from typing import Tuple, List
from dataclasses import dataclass
import time
import sys

class TokenDoesNotExistException(Exception): pass


@dataclass
class TokenObj:
    token: str
    exp: int
    scope: List[str]

    def is_expired(self):
        exp_utc_seconds = self.exp
        now_tc_seconds = time.time()
        return now_tc_seconds > exp_utc_seconds

def decode_jwt(token:str):    
    hdr, info, sig = token.split('.')
    info_json = json.loads(base64.b64decode(info + '==').decode('utf-8'))
    hdr_json = json.loads(base64.b64decode(hdr + '==').decode('utf-8'))
    return hdr_json, info_json, sig

def get_current_token() -> TokenObj:
    if token_path.exists():
        with open(token_path, "r") as fp:
            token=fp.read()
            hdr, info, sig = decode_jwt(token)
        return TokenObj(
            token=token,
            exp=info.get("exp"),
            scope=info.get("scope").split(" "))
    raise TokenDoesNotExistException

def delete_curr_token():
    if token_path.exists():
        token_path.unlink()
    

@click.group()
def auth():
    pass

@click.command()
@click.option("--scope", help="Comma separated additional scopes to ask for. e.g. profile,group,team,email")
@click.option("--force", "-f", help="Do not check existing token.", is_flag=True)
@click.option("--print", "-p", help="Print token to stdout.", is_flag=True)
def login(scope:str, force: bool, p: bool):
    parsed_scopes=[scope for scope in (scope or "").split(",") if scope]
    if not force:
        try:
            token_inst = get_current_token()
            token_expired_flag = token_inst.is_expired()
            
            if token_expired_flag:
                raise TokenDoesNotExistException
            
            not_included_scope = [s for s in parsed_scopes if (s not in token_inst.scope)]
            if len(not_included_scope) == 0:
                print("Current token can be reused.")
                return
            print(f"Requested scopes {not_included_scope} is not in the current token's scopes {token_inst.scope}. Rerequesting...")

        except TokenDoesNotExistException:
            pass

    token_path.parent.mkdir(exist_ok=True, parents=True)
    token = start_device_flow(scope=parsed_scopes)
    with open(token_path, "w") as fp:
        fp.write(token)
        if p:
            print(token)
    print("Auth successful!")

auth.add_command(login, "login")

@click.command()
def logout():
    delete_curr_token()

auth.add_command(logout, "logout")

@click.command()
@click.option("--ignore-expiry", "-i", help="Do not try to check expiry.", is_flag=True)
def _print(ignore_expiry):
    try:
        token = get_current_token()
        if not ignore_expiry:
            if token.is_expired():
                print("Token expired")
                sys.exit(1)
                
        print(token.token)
    except TokenDoesNotExistException:
        print("Token not found.")
        sys.exit(1)

auth.add_command(_print, "print")

__all__ = [
    "start_device_flow",
    "ClientCredentialsSession",
    "auth",
    "decode_jwt",
    "get_current_token",
    "TokenDoesNotExistException"
]
