from ebrains_drive import BucketApiClient
import click
import sys
import json
from dataclasses import dataclass
import requests
import tqdm
from pathlib import Path
import shutil
from typing import Union, Callable
from io import IOBase
import os
from io import BytesIO
from typing import List

@dataclass
class CtxBucket:
    bucket_name: str

    def get_bucket(self):
        from ..iam import get_current_token, TokenDoesNotExistException
        try:
            _token = get_current_token()
            token = None if _token.is_expired() else _token.token
        except TokenDoesNotExistException:
            token = None
        if token is None:
            print("Not authenticated. Using anonymous client. Only has read access to public buckets", file=sys.stderr)
        client = BucketApiClient(token=token)
        return client.buckets.get_bucket(self.bucket_name)

pass_bucket = click.make_pass_decorator(CtxBucket)

@click.group()
@click.option("--bucket-name", "-n", required=True, type=str, help="Name of the bucket.")
@click.pass_context
def bucket(ctx, bucket_name: str):
    """Bucket API (ls/upload/download)"""
    ctx.obj = CtxBucket(bucket_name=bucket_name)


@click.command()
@click.option("--prefix", help="Prefix to filter the ls result", type=str)
@click.option("--json", "jsonflag", help="Output as JSON", is_flag=True)
@pass_bucket
def ls(bucket_ctx: CtxBucket, prefix: str, jsonflag: bool):
    """List files."""
    bucket = bucket_ctx.get_bucket()
    all_names = [f.name for f in bucket.ls(prefix=prefix)]
    if len(all_names) == 0:
        print("Could not find any file.", file=sys.stderr)
        return
    if jsonflag:
        print(json.dumps(all_names))
        return
    print("\n".join(all_names))

bucket.add_command(ls, "ls")

def get_dest_file(filename: str, dest: str, force=False) -> Path:

    _dest = Path(dest or ".")

    if _dest.exists():
        if _dest.is_dir():
            return _dest / Path(filename).name
        if force:
            return _dest
        raise RuntimeError(f"Dest {str(dest)} already exists")
    
    if _dest.name.endswith("/"):
        _dest.mkdir(parents=True)
        return _dest / Path(filename).name
    
    return _dest


@click.command()
@click.option("--force", help="Overwrite file if exists.", is_flag=True)
@click.argument("filename", required=True, type=str)
@click.argument("dest", required=False, type=str)
@pass_bucket
def download(bucket_ctx: CtxBucket, filename: str, dest: str, force: bool):
    """Download file.
    
    Set dest to - to stream to stdout."""

    stream_to_stdout = dest == "-"

    bucket = bucket_ctx.get_bucket()
    file = bucket.get_file(filename)
    link = file.get_download_link()
    
    resp = requests.get(link, stream=True)
    resp.raise_for_status()
    total_size = resp.headers.get("content-length") and int(resp.headers.get("content-length"))

    if not stream_to_stdout:
        dest_file = get_dest_file(filename, dest)
        tmp_dest_file = dest_file.with_stem(f"tmp_{dest_file.name}")
        fh = open(tmp_dest_file, "wb")
        progress = tqdm.tqdm(total=total_size) if total_size else tqdm.tqdm()
    else:
        fh = sys.stdout

    try:
        for data in resp.iter_content(chunk_size=4096):
            fh.write(data.decode("utf-8") if stream_to_stdout else data)
            
            if not stream_to_stdout:
                progress.update(4096)

        if not stream_to_stdout:
            fh.close()
            shutil.copy(tmp_dest_file, dest_file)
    except Exception as e:
        print(f"Downloading file failed: {str(e)}", file=sys.stderr)
    finally:
        if not stream_to_stdout:
            if not fh.closed:
                fh.close()
            tmp_dest_file.unlink()

bucket.add_command(download, "download")

class ProgressReader(IOBase):
    def __init__(self, file: Union[str, Path], update: Callable) -> None:
        super().__init__()
        self.fh = open(file, "rb")
        self.size = Path(file).stat().st_size
        self.update = update
    
    def __len__(self):
        return self.size

    def read(self, n):
        self.update(n)
        return self.fh.read(n)

    def close(self):
        self.fh.close()

@click.command()
@click.option("--progress", help="Show progress of upload. Cannot be used with stdin", is_flag=True)
@click.option("--header", "-H", required=False, type=str, multiple=True, help="Add custom headers on upload. Similar to curl usage. Can be set multiple times")
@click.argument("filename", required=True, type=str)
@click.argument("dest", required=True, type=str)
@pass_bucket
def upload(bucket_ctx: CtxBucket, filename: str, dest: str, progress: bool, header: List[str]):
    """Upload file.
    
    Use - at filename to read from stdin"""
    bucket = bucket_ctx.get_bucket()

    headers = {}
    for hdr in header:
        try:
            header_name, header_value = hdr.split(":", 1)
            headers[header_name] = header_value.strip()
        except ValueError as e:
            raise ValueError("header must be in the format of [header_name]:[header_value]") from e

    if progress:
        if filename == "-":
            raise Exception(f"progress flag cannot be used with stdin")
        fh = ProgressReader(filename, lambda n: print("updated", n))
        with tqdm.tqdm(total=fh.size) as tqdmp:
            fh.update = lambda n: tqdmp.update(n)
            bucket.upload(fh, dest, headers=headers)
    else:
        if filename == "-":
            filename = BytesIO(sys.stdin.buffer.read())
            filename.seek(0)
        bucket.upload(filename, dest, headers=headers)

bucket.add_command(upload, "upload")


@click.command()
@click.option("--hash", "hash_flag", help="Hash directory first. This helps reduce duplicated work for multiple duplicated directories.", is_flag=True)
@click.argument("srcpath", required=True, type=str)
@click.argument("dstpath", required=False, default=".", type=str)
@pass_bucket
def sync(bucket_ctx: CtxBucket, hash_flag: bool, srcpath: str, dstpath: str):
    """Sync directory/file."""
    if hash_flag:
        from ebrains_dataproxy_sync.hash.hash import hash_dir
        hash_dir(Path(srcpath))

    prev_auth_token = os.environ.get("AUTH_TOKEN")
    try:
        from ebrains_dataproxy_sync.sync.dataproxy import sync
        from ..iam import get_current_token
        token = get_current_token()
        os.environ["AUTH_TOKEN"] = token.token
        sync(bucket_ctx.bucket_name, Path(srcpath), dstpath)
    except Exception as e:
        print(f"Sync failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.environ.pop("AUTH_TOKEN", None)
        if prev_auth_token:
            os.environ["AUTH_TOKEN"] = prev_auth_token
            
bucket.add_command(sync, "sync")
