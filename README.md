# EBRAINS util

## Installation

```sh
pip install git+https://github.com/xgui3783/ebrains-util.git
```


## Usage

```python
import os
from ebrains_util import iam, kg, dataproxy
from pathlib import Path

token = iam.start_device_flow(scope=["team"])
os.environ["AUTH_TOKEN"] = token

path_to_my_dir = Path("my-dir")
path_to_my_file = Path("my-dir2/test.txt")

dataproxy.dataproxy_sync("my-bucket", path_to_my_dir)
dataproxy.dataproxy_sync("my-bucket", path_to_my_file)

```

or from command line:

```sh

echo "hello world" > foo.bar

# team is needed for dataproxy!
ebrains_util iam auth login --scope team
ebrains_util bucket -n MY_BUCKET_NAME upload foo.bar dest/foo.bar

```

If you would like the auth token to be stored/used from a different path, set `EBRAINS_UTIL_USER_PATH` env var.

## Download from / Upload to dataproxy:

```sh

# download public file
ebrains_util download https://data-proxy.ebrains.eu/api/v1/buckets/my-public-bucket/file.txt

# download private file
ebrains_util iam auth login --scope team
ebrains_util download https://data-proxy.ebrains.eu/api/v1/buckets/my-private-bucket/file.txt

# upload from stdin
# n.b. ?inline=true is **required**!
ebrains_util iam auth login --scope team
echo "fuzzbuzz" | ebrains_util upload https://data-proxy.ebrains.eu/api/v1/buckets/my-bucket/text.txt?inline=true -


# upload file to different filename
ebrains_util iam auth login --scope team
ebrains_util upload https://data-proxy.ebrains.eu/api/v1/buckets/my-bucket/my-folder/mybestfile.txt?inline=true myfile.txt

# upload file to directory
ebrains_util iam auth login --scope team
ebrains_util upload https://data-proxy.ebrains.eu/my-bucket?prefix=my_directory%2F myfile.txt

# upload file
ebrains_util iam auth login --scope team
ebrains_util upload https://data-proxy.ebrains.eu/my-bucket myfile.txt

# relative path is preseved!
ebrains_util iam auth login --scope team
ebrains_util upload https://data-proxy.ebrains.eu/my-bucket my_directory/myfile.txt
# artefact will be uploaded to https://data-proxy.ebrains.eu/api/v1/buckets/my-bucket/my_directory/myfile.txt

```

## Shell completion

`ebrains_util` uses click. Per [click's documentation](https://click.palletsprojects.com/en/stable/shell-completion/), to use `ebrains_util` shell completion (e.g. `<tab>` to get autocomplete suggestions):

```sh
eval "$(_EBRAINS_UTIL_COMPLETE=bash_source ebrains_util)"
```

## License

MIT
