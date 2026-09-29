"""Constructor interface used from session-adapters 0.5.0."""
from requests.adapters import BaseAdapter

class S3Adapter(BaseAdapter):
    def __init__(self, region_name: str | None = ..., aws_access_key_id: str | None = ..., aws_secret_access_key: str | None = ..., aws_session_token: str | None = ..., endpoint_url: str | None = ..., config: object | None = ...) -> None: ...
