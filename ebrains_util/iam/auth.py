import json
import click
import base64
from typing import List
from dataclasses import dataclass
import time
import sys
from functools import wraps
from typing import Callable

from ebrains_iam.device_flow import start as start_device_flow
from ebrains_iam.refresh import smart_refresh
from ebrains_iam.client_credential import ClientCredentialsSession

from ..config import (
    token_path,
    EBRAINS_UTIL_AUTH_TOKEN,
    EBRAINS_UTIL_CLIENT_ID,
    EBRAINS_UTIL_CLIENT_SECRET,
    EBRAINS_UTIL_REFRESH_TOKEN,
    EBRAINS_UTIL_TOKEN_SCOPE,
)

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
    
    @classmethod
    def from_str(cls, token_str: str):
        hdr, info, sig = decode_jwt(token_str)
        return cls(
            token=token_str,
            exp=info.get("exp"),
            scope=info.get("scope").split(" "))

def decode_jwt(token:str):    
    hdr, info, sig = token.split('.')
    info_json = json.loads(base64.b64decode(info + '==').decode('utf-8'))
    hdr_json = json.loads(base64.b64decode(hdr + '==').decode('utf-8'))
    return hdr_json, info_json, sig

def str_to_token(cache_to_file: bool=True):
    def outer(fn: Callable[[], str]):
        @wraps(fn)
        def inner(*args, **kwargs):
            token_str = fn(*args, **kwargs)
            if not token_str:
                return
            token = TokenObj.from_str(token_str)
            if not token.is_expired():
                if cache_to_file:
                    token_path.parent.mkdir(exist_ok=True, parents=True, mode=0o700)
                    token_path.write_text(token_str)
                return token
        return inner
    return outer

@str_to_token()
def _get_token_refreshed():
    if EBRAINS_UTIL_REFRESH_TOKEN and EBRAINS_UTIL_CLIENT_ID:
        token, refresh_token, refreshed = smart_refresh(EBRAINS_UTIL_REFRESH_TOKEN, EBRAINS_UTIL_CLIENT_ID)
        return token

@str_to_token()
def _get_token_s2s():
    if EBRAINS_UTIL_CLIENT_ID and EBRAINS_UTIL_CLIENT_SECRET:
        sess = ClientCredentialsSession(EBRAINS_UTIL_CLIENT_ID, EBRAINS_UTIL_CLIENT_SECRET, scope=EBRAINS_UTIL_TOKEN_SCOPE.split(" ") or [])
        token = sess.get_token()
        return token

@str_to_token(cache_to_file=False)
def _get_token_file():
    if token_path.exists():
        
        with open(token_path, "r") as fp:
            return fp.read()

@str_to_token()
def _get_token_env():
    if EBRAINS_UTIL_AUTH_TOKEN:
        return EBRAINS_UTIL_AUTH_TOKEN

def get_current_token() -> TokenObj:
    token = _get_token_file()
    if token:
        return token
    
    token = _get_token_env()
    if token:
        return token
    
    token = _get_token_s2s()
    if token:
        return token
    
    token = _get_token_refreshed()
    if token:
        return token
    
    raise TokenDoesNotExistException

def delete_curr_token():
    if token_path.exists():
        token_path.unlink()
    

@click.group()
def auth():
    """Everthing auth related (login/logout, print/debug/set token)"""
    pass

@click.command()
@click.argument("token", required=True, type=str)
def set_token(token: str):
    """Set token"""
    token_path.parent.mkdir(exist_ok=True, parents=True, mode=0o700)
    token_path.write_text(token)

auth.add_command(set_token, "set-token")

@click.command()
@click.option("--scope", help="Comma separated additional scopes to ask for. e.g. profile,group,team,email")
@click.option("--force", "-f", help="Do not check existing token.", is_flag=True)
@click.option("--print", "printflag", help="Print token to stdout. Will not save. (Useful for one time generation of token)", is_flag=True)
@click.option("--client-id", help="client-id for client credential flow")
@click.option("--client-secret", help="client-secret for client credential flow")
def login(scope:str, force: bool, printflag: bool, client_id: str, client_secret: str):
    """Login (via siibra)
    
    if --client-id is provided, will overwrite the default client-id (siibra)
    if --client-secret is provided, will use client credential flow
    otherwise will use device flow."""
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

    token_path.parent.mkdir(exist_ok=True, parents=True, mode=0o700)
    if client_id and client_secret:
        sess = ClientCredentialsSession(client_id, client_secret, scope=parsed_scopes)
        token = sess.get_token()
    else:
        token = start_device_flow(scope=parsed_scopes, client_id=client_id)

    if printflag:
        print(token)
        return
    token_path.write_text(token)    
    print("Auth successful!", file=sys.stderr)

auth.add_command(login, "login")

@click.command()
def logout():
    """Logout"""
    delete_curr_token()

auth.add_command(logout, "logout")

@click.command()
@click.option("--ignore-expiry", "-i", help="Do not try to check expiry.", is_flag=True)
@click.option("--decode", help="Decode jwt", is_flag=True)
def _print(ignore_expiry, decode):
    """Print token"""
    try:
        token = get_current_token()
        if not ignore_expiry:
            if token.is_expired():
                print("Token expired", file=sys.stderr)
                sys.exit(1)
        if decode:
            hdr_json, info_json, sig = decode_jwt(token.token)
            print(json.dumps(hdr_json, indent=2))
            print("=====")
            print(json.dumps(info_json, indent=2))
            print("=====")
            print(sig)
            return
        print(token.token)
    except TokenDoesNotExistException:
        print("Token not found.", file=sys.stderr)
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
