"""Constructor interface used from session-adapters 0.5.0."""
from requests.adapters import HTTPAdapter

class BearerAuthHTTPAdapter(HTTPAdapter):
    def __init__(self, token: str) -> None: ...
