from urllib.parse import parse_qsl, urlparse

_DATAPROXY_UI_PREFIX = "https://data-proxy.ebrains.eu/"
_DATAPROXY_API_PREFIX = f"{_DATAPROXY_UI_PREFIX}api/v1/buckets/"

def parse_dataproxy_url(url: str) -> tuple[str, str, str]:
    """
    Given a data-proxy public URL, return bucket-id, prefix (or None), filepath (or None) as a tuple

    Parameters
    ----------
    url: str
        - direct path to object (e.g. https://data-proxy.ebrains.eu/api/v1/buckets/p22717-hbp-d000045_receptors-human-hOc1_pub/v1.0/receptors.tsv)
        - direct path to object, as copied from KG (e.g. https://data-proxy.ebrains.eu/api/v1/buckets/p22717-hbp-d000045_receptors-human-hOc1_pub/v1.0/receptors.tsv?inline=true)
        - URL of bucket from data proxy UI (e.g. https://data-proxy.ebrains.eu/p22717-hbp-d000045_receptors-human-hOc1_pub/ )
        - traversed URL of bucket from data proxy UI (e.g. https://data-proxy.ebrains.eu/p22717-hbp-d000045_receptors-human-hOc1_pub/?prefix=v1.0%2FhOc1_ar_examples%2F5-HT1A%2F)
        - bucket-id (no / in str)

    Returns
    -------
    tuple[str, str|None, str|None]
        bucket-id, prefix (only applicable for URL from UI), filepath (only applicable for direct path)

    Raises
    ------
    NotImplementedError
        if url does not start with prescribed prefix
    RunTimeError
        if the URL is malformed
    """
    if url.startswith(_DATAPROXY_API_PREFIX):
        url = url.removeprefix(_DATAPROXY_API_PREFIX)
        url = url.removesuffix("?inline=true")
        bucket_id, *filepaths = url.split("/", 1)
        return tuple((bucket_id, None, "".join(filepaths)))
    if url.startswith(_DATAPROXY_UI_PREFIX):
        parsed = urlparse(url)
        bucket_id, *_ = parsed.path.removeprefix("/").split("/", maxsplit=1)
        if bucket_id == "":
            raise RuntimeError(f"{url=} does not have a valid path")
        path = dict(parse_qsl(parsed.query))
        prefix = path.get("prefix", "")
        return tuple((bucket_id, prefix, None))
    if "/" not in url:
        return tuple((url, None, None))
    raise NotImplementedError(
        f"url must start with either {_DATAPROXY_API_PREFIX} or {_DATAPROXY_UI_PREFIX}"
    )
