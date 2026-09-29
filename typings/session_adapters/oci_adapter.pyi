"""Constructor interface used from session-adapters 0.5.0."""
from requests.adapters import BaseAdapter

class OCIAdapter(BaseAdapter):
    def __init__(self, hostname: str | None = ..., username: str | None = ..., password: str | None = ...) -> None: ...
