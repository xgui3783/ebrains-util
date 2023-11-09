# EBRAINS util

## Installation

```sh

# important! must install version_query first, or installation will not succeed
pip install version_query
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

## License

MIT
