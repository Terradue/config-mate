"""Content types and headers from session-adapters 0.5.0."""
from enum import Enum

DEFAULT_ENCODING: str

class HTTPHeader(str, Enum):
    CONTENT_TYPE = "Content-Type"

class ContentType(str, Enum):
    # --- Text ---
    PLAIN = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    CSV = "text/csv"
    TEXT_JAVASCRIPT = "text/javascript"
    TEXT_YAML = "text/yaml"  # gh-pages on github serves "text/yaml"
    MARKDOWN = "text/markdown"
    XML_TEXT = "text/xml"

    # --- Application / structured text ---
    JSON = "application/json"
    PROBLEM_JSON = "application/problem+json"
    SCHEMA_JSON = "application/schema+json"
    XML = "application/xml"
    YAML = "application/x-yaml"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    OCTET_STREAM = "application/octet-stream"
    PDF = "application/pdf"
    ZIP = "application/zip"
    GZIP = "application/gzip"
    TAR = "application/x-tar"
    RTF = "application/rtf"
    APPLICATION_JAVASCRIPT = "application/javascript"

    # --- Multipart ---
    MULTIPART_FORM = "multipart/form-data"
    MULTIPART_MIXED = "multipart/mixed"
    MULTIPART_ALTERNATIVE = "multipart/alternative"
    MULTIPART_RELATED = "multipart/related"

    # --- Images ---
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"
    TIFF = "image/tiff"
    BMP = "image/bmp"
    ICON = "image/x-icon"

    # --- Audio ---
    MP3 = "audio/mpeg"
    OGG = "audio/ogg"
    WAV = "audio/wav"
    WEBM_AUDIO = "audio/webm"

    # --- Video ---
    MP4 = "video/mp4"
    MPEG = "video/mpeg"
    OGG_VIDEO = "video/ogg"
    WEBM_VIDEO = "video/webm"
    QUICKTIME = "video/quicktime"

    # --- Fonts ---
    WOFF = "font/woff"
    WOFF2 = "font/woff2"
    TTF = "font/ttf"
    OTF = "font/otf"

    # --- Misc / Special ---
    ANY = "*/*"

