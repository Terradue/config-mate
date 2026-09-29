"""Constructor interface used from session-adapters 0.5.0."""
from requests.adapters import BaseAdapter

class FileAdapter(BaseAdapter):
    def __init__(self) -> None: ...
