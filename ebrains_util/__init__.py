import sys
from io import BytesIO
from pathlib import Path

import click
import requests
from ebrains_drive import BucketApiClient

from .iam import iam, get_current_token
from .bucket import bucket, parse_dataproxy_url
from .ingestion import ing
from .config import EBRAINS_UTIL_CHUNK_SIZE


@click.group()
def cli():
    """CLI to interact with ebrains services."""
    pass


cli.add_command(iam, "iam")

cli.add_command(bucket, "bucket")

cli.add_command(ing, "ing")


@click.command()
@click.argument("url", required=True, type=str)
def _express_download(url: str):
    """Download a file given a URL. Will try public link, if fails, use token."""
    bucketname, _, fname = parse_dataproxy_url(url)
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()

        with open(fname, "wb") as fp:
            for chunk in resp.iter_content(EBRAINS_UTIL_CHUNK_SIZE):
                fp.write(chunk)
        print(f"Successfully downloaded {url}", file=sys.stderr)
        return
    except requests.HTTPError:
        ...
    print("Direct download failed. Using token download", file=sys.stderr)
    token = get_current_token()
    client = BucketApiClient(token=token)
    bucket = client.buckets.get_bucket(bucketname)
    link: str = bucket.get_file(fname).get_download_link()

    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    with open(fname, "wb") as fp:
        for chunk in resp.iter_content(EBRAINS_UTIL_CHUNK_SIZE):
            fp.write(chunk)
    print(f"Successfully downloaded {url}", file=sys.stderr)
    return


@click.command()
@click.argument("url", required=True, type=str)
@click.argument("file", required=True, type=str)
def _express_upload(url: str, file: str):
    """Upload a file. Use - at filename to read from stdin."""
    bucketname, fpath, fname = parse_dataproxy_url(url)

    token = get_current_token()
    client = BucketApiClient(token=token.token)
    bucket = client.buckets.get_bucket(bucketname)
    if file == "-":
        print("Reading stdin for upload", file=sys.stderr)
        file = BytesIO(sys.stdin.buffer.read())
        file.seek(0)

    if fname:
        print(f"Uploading to {bucketname=} {fname=}", file=sys.stderr)
        bucket.upload(file, fname)
        print("Success!", file=sys.stderr)
        return

    if fpath is None:
        fpath = ""

    assert not isinstance(
        file, BytesIO
    ), f"dir upload must either contain ?inline=true or use filename"
    upload_path = f"{fpath}{Path(file).name}"
    print(f"Uploading to {bucketname=} {upload_path=}", file=sys.stderr)
    bucket.upload(file, upload_path)
    print("Success!", file=sys.stderr)


cli.add_command(_express_download, "download")
cli.add_command(_express_upload, "upload")
