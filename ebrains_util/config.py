from pathlib import Path
import os

EBRAINS_UTIL_USER_PATH = os.getenv("EBRAINS_UTIL_USER_PATH", os.path.expanduser("~/.ebrains_util"))

token_path = Path(EBRAINS_UTIL_USER_PATH) / "auth_token"
