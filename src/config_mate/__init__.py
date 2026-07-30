# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This workflow will install Python dependencies, run tests and lint with a single version of Python
# For more information see: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

from collections.abc import Mapping
from gzip import GzipFile
from io import BytesIO, StringIO, TextIOWrapper
from pathlib import Path
from typing import Any, TextIO, final
from urllib.parse import urlparse

import requests
from jsonref import replace_refs
from loguru import logger
from requests.adapters import BaseAdapter
from session_adapters.http_conts import DEFAULT_ENCODING, ContentType, HTTPHeader

from .handlers import StreamHandler
from .handlers.json_handler import JsonHandler
from .handlers.xml_handler import XmlHandler
from .handlers.yaml_handler import YamlHandler


@final
class ConfigMate:
    def __init__(self):
        self.session = requests.Session()

        logger.debug("All supported schemes mounted")

        self.handlers = {}

        logger.debug(
            "Handlers registry initialized, mounting default supported handlers..."
        )

        json_handler = JsonHandler()
        self.mount_handler(ContentType.JSON, json_handler)
        self.mount_handler(ContentType.PROBLEM_JSON, json_handler)
        self.mount_handler(ContentType.SCHEMA_JSON, json_handler)

        xml_handler = XmlHandler()
        self.mount_handler(ContentType.XML, xml_handler)
        self.mount_handler(ContentType.XML_TEXT, xml_handler)

        yaml_handler = YamlHandler()
        self.mount_handler(
            ContentType.PLAIN, yaml_handler
        )  # GitHub RAW uses to reply back 'text/plain'
        self.mount_handler(ContentType.YAML, yaml_handler)
        self.mount_handler(ContentType.TEXT_YAML, yaml_handler)

        logger.debug("All supported handlers mounted")

    def mount_session(self, scheme: str, adapter: BaseAdapter):
        logger.debug(f"Mounting '{scheme}' scheme to '{type(adapter).__name__}'...")
        self.session.mount(scheme, adapter)
        logger.debug(
            f"Scheme '{scheme}' successfully mount to '{type(adapter).__name__}'"
        )

    def mount_handler(self, content_type: ContentType | str, handler: StreamHandler):
        mime_type = (
            content_type.value
            if isinstance(content_type, ContentType)
            else content_type
        )
        logger.debug(
            f"Mounting '{mime_type}' mime-type to '{type(handler).__name__}'..."
        )
        self.handlers[content_type] = handler
        logger.debug(
            f"mime-type '{mime_type}' successfully mount to '{type(handler).__name__}'"
        )

    def _get_handler(self, content_type: ContentType | str) -> StreamHandler:
        handler = self.handlers.get(content_type)
        mime_type = (
            content_type.value
            if isinstance(content_type, ContentType)
            else content_type
        )

        if not handler:
            raise ValueError(
                f"{mime_type} can not be handled, please provide a {StreamHandler} implementation that cab handle {mime_type}."
            )

        logger.debug(f"Handling {mime_type} with {type(handler).__name__}")

        return handler

    def _is_valid_url(self, path_or_url: str):
        try:
            url_parts = urlparse(path_or_url)
            return url_parts.scheme
        except Exception:
            return False

    def load_config_from_dict(
        self, config_dict: Mapping[str, Any], base_uri: str = ""
    ) -> Mapping[str, Any]:
        """
        Build a Config from a Mapping (top-level must be a Mapping).

        Args:
            `config_dict` (`Mapping[str, Any]`): The configuration in a dictionary.

        Returns:
            `Mapping[str, Any]`: The configuration Document Object Model.
        """
        logger.debug("Resolving all the JSON Reference...")

        referenced_dict = replace_refs(
            config_dict,
            base_uri=base_uri,
            lazy_load=False,
            load_on_repr=False,
            proxies=False,  # Resolve $ref into *plain* Python structures
            loader=self.load_config_from_location,
            jsonschema=False,
            merge_props=True,
        )

        logger.debug(
            f"All the JSON Reference for document {base_uri} successfully resolved as '{type(referenced_dict).__name__}'!"
        )

        return referenced_dict  # type: ignore

    def load_config_from_stream(
        self,
        config_stream: TextIO,
        content_type: ContentType | str = ContentType.YAML,
        base_uri: str = "",
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        """
        Read YAML from a text stream and build a Config.

        Args:
            `config_stream` (`TextIOBase`): The stream where reading the configuration representation.

        Returns:
            `Mapping[str, Any]`: The configuration Document Object Model.
        """
        mime_type = (
            content_type.value
            if isinstance(content_type, ContentType)
            else content_type
        )
        logger.debug(f"Loading configuration from {mime_type} Input Stream...")

        handler = self._get_handler(content_type)
        loaded = handler.handle(config_stream)

        if loaded is None:
            raise ValueError(f"{mime_type} content is empty.")

        if isinstance(loaded, list):
            return [
                self.load_config_from_dict(
                    config_dict=current_loaded, base_uri=base_uri
                )
                for current_loaded in loaded
            ]

        return self.load_config_from_dict(config_dict=loaded, base_uri=base_uri)

    def load_config_from_content(
        self,
        config_content: str,
        content_type: ContentType = ContentType.YAML,
        base_uri: str = "",
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        """
        Read configuration from a string.

        Args:
            `config_stream` (`TextIOBase`): The string where reading the configuration representation.

        Returns:
            `Mapping[str, Any]`: The configuration Document Object Model.
        """
        logger.debug("Loading configuration from string content ...")

        return self.load_config_from_stream(
            config_stream=StringIO(config_content),
            content_type=content_type,
            base_uri=base_uri,
        )

    def load_config_from_location(
        self, config_location: str
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        """
        Read configuration from a local File System location or URL.

        Args:
            `config_location` (`str`): The location on the Fyle System or the URL where reading the configuration YAML representation.

        Returns:
            `Mapping[str, Any]`: The configuration Document Object Model.
        """
        if self._is_valid_url(config_location):
            logger.debug(f"> GET {config_location}...")

            response = self.session.get(config_location, stream=True)
            response.raise_for_status()

            logger.debug(f"< {response.status_code} {response.reason}")
            for k, v in response.headers.items():
                logger.debug(f"< {k}: {v}")

            # Read first 2 bytes to check for gzip
            magic = response.raw.read(2)
            remaining = response.raw.read()  # Read rest of the stream
            combined = BytesIO(magic + remaining)
            buffer: BytesIO | GzipFile

            if magic == b"\x1f\x8b":
                logger.debug(
                    f"gzip compression detected in response body from {config_location}"
                )
                buffer = GzipFile(fileobj=combined)
            else:
                buffer = combined

            logger.debug(
                f"Reading content obtained from {config_location} response body..."
            )

            content_type = response.headers.get(HTTPHeader.CONTENT_TYPE.value)
            if not content_type:
                content_type = ContentType.YAML
                # raise ValueError(f"Unknown Content Type {content_type}, loader is not able to handle it")

            if ";" in content_type:
                content_type = content_type.split(";")[0]

            return self.load_config_from_stream(
                config_stream=TextIOWrapper(buffer, encoding=DEFAULT_ENCODING),
                base_uri=config_location,
                content_type=content_type,
            )

        if not Path(config_location).exists():
            raise ValueError(
                f"Invalid source {config_location}, resource does not exist on the File System"
            )

        config_location_url = Path(config_location).resolve().absolute().as_uri()

        logger.debug(
            f"{config_location} detected as local File System location; following up to {config_location_url}..."
        )

        return self.load_config_from_location(config_location_url)

    def dump_config(
        self,
        configuration: Mapping[str, Any] | list[Mapping[str, Any]],
        stream: TextIO,
        content_type: ContentType = ContentType.YAML,
    ):
        handler = self._get_handler(content_type)

        handler.write(configuration, stream)
