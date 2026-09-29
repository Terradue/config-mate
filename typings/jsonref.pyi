"""Reference resolution interface from jsonref 1.1.0."""

from collections.abc import Callable

def replace_refs(
    obj: object,
    base_uri: str = ...,
    loader: Callable[[str], object] = ...,
    jsonschema: bool = ...,
    load_on_repr: bool = ...,
    merge_props: bool = ...,
    proxies: bool = ...,
    lazy_load: bool = ...,
) -> object: ...
