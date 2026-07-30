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

import gzip
from io import BytesIO, StringIO
from unittest.mock import Mock

import pytest
from requests.adapters import BaseAdapter
from session_adapters.http_conts import ContentType

from config_mate import ConfigMate
from config_mate.handlers import StreamHandler
from config_mate.handlers.json_handler import JsonHandler
from config_mate.handlers.xml_handler import XmlHandler
from config_mate.handlers.yaml_handler import YamlHandler


class StubResponse:
    def __init__(
        self,
        body: bytes,
        content_type: str | None = None,
        status_code: int = 200,
    ):
        self.raw = BytesIO(body)
        self.headers = {}
        if content_type is not None:
            self.headers["Content-Type"] = content_type
        self.status_code = status_code
        self.reason = "OK"
        self.raise_for_status = Mock()


class EchoHandler(StreamHandler):
    def handle(self, stream):
        return {"value": stream.read()}

    def write(self, configuration, stream):
        stream.write(configuration["value"])


def test_default_handlers_are_registered_for_supported_aliases():
    mate = ConfigMate()

    assert isinstance(mate._get_handler(ContentType.JSON), JsonHandler)
    assert mate._get_handler(ContentType.JSON) is mate._get_handler(
        ContentType.PROBLEM_JSON
    )
    assert mate._get_handler(ContentType.JSON) is mate._get_handler(
        ContentType.SCHEMA_JSON
    )
    assert isinstance(mate._get_handler(ContentType.XML), XmlHandler)
    assert mate._get_handler(ContentType.XML) is mate._get_handler(ContentType.XML_TEXT)
    assert isinstance(mate._get_handler(ContentType.YAML), YamlHandler)
    assert mate._get_handler(ContentType.YAML) is mate._get_handler(ContentType.PLAIN)


def test_custom_handler_can_be_mounted_and_used_for_load_and_dump():
    mate = ConfigMate()
    mate.mount_handler(ContentType.CSV, EchoHandler())

    assert mate.load_config_from_content("example", ContentType.CSV) == {
        "value": "example"
    }

    output = StringIO()
    mate.dump_config({"value": "rendered"}, output, ContentType.CSV)
    assert output.getvalue() == "rendered"


def test_unregistered_content_type_is_rejected():
    with pytest.raises(ValueError, match="text/html can not be handled"):
        ConfigMate()._get_handler(ContentType.HTML)


def test_session_adapter_can_be_mounted():
    mate = ConfigMate()
    adapter = Mock(spec=BaseAdapter)

    mate.mount_session("custom://", adapter)

    assert mate.session.adapters["custom://"] is adapter


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("https://example.test/config.yaml", "https"),
        ("file:///tmp/config.yaml", "file"),
        ("relative/config.yaml", ""),
    ],
)
def test_url_detection(location, expected):
    assert ConfigMate()._is_valid_url(location) == expected


def test_url_detection_returns_false_when_parsing_fails(monkeypatch):
    def fail(_location):
        raise ValueError("bad URL")

    monkeypatch.setattr("config_mate.urlparse", fail)

    assert ConfigMate()._is_valid_url("anything") is False


def test_load_dict_resolves_internal_json_references_to_plain_values():
    source = {
        "definitions": {"defaults": {"retries": 3}},
        "service": {"$ref": "#/definitions/defaults"},
    }

    loaded = ConfigMate().load_config_from_dict(source)

    assert loaded["service"] == {"retries": 3}
    assert type(loaded["service"]) is dict


def test_load_content_selects_handler_and_resolves_references():
    loaded = ConfigMate().load_config_from_content(
        '{"definitions": {"port": 8080}, "port": {"$ref": "#/definitions/port"}}',
        ContentType.JSON,
        base_uri="https://example.test/config.json",
    )

    assert loaded["port"] == 8080


def test_resolved_references_are_dumped_to_yaml_without_anchors_or_aliases():
    mate = ConfigMate()
    loaded = mate.load_config_from_content(
        """
defaults:
  retries: 3
services:
  api:
    $ref: "#/defaults"
  worker:
    $ref: "#/defaults"
"""
    )
    output = StringIO()

    mate.dump_config(loaded, output)

    rendered = output.getvalue()
    assert "&id" not in rendered
    assert "*id" not in rendered
    assert rendered.count("retries: 3") == 3


def test_empty_json_content_is_rejected():
    with pytest.raises(ValueError, match="application/json content is empty"):
        ConfigMate().load_config_from_content("null", ContentType.JSON)


@pytest.mark.parametrize(
    ("body", "content_type", "expected"),
    [
        (b'{"name": "json"}', "application/json; charset=utf-8", {"name": "json"}),
        (b"name: yaml\n", None, {"name": "yaml"}),
    ],
)
def test_load_url_uses_response_content_type_or_yaml_default(
    body, content_type, expected
):
    mate = ConfigMate()
    response = StubResponse(body, content_type)
    mate.session.get = Mock(return_value=response)

    loaded = mate.load_config_from_location("https://example.test/config")

    assert loaded == expected
    mate.session.get.assert_called_once_with("https://example.test/config", stream=True)
    response.raise_for_status.assert_called_once_with()


def test_external_yaml_references_resolve_to_documents_not_document_arrays():
    mate = ConfigMate()
    referenced_documents = {
        "https://example.test/stage-in.cwl": b"class: CommandLineTool\nid: stage-in\n",
        "https://example.test/workflow.cwl": b"class: Workflow\nid: workflow\n",
        "https://example.test/stage-out.cwl": b"class: CommandLineTool\nid: stage-out\n",
    }

    def get(location, stream):
        assert stream is True
        return StubResponse(referenced_documents[location], "text/plain")

    mate.session.get = Mock(side_effect=get)

    loaded = mate.load_config_from_content(
        """
workflows:
  directory_stage_in:
    $ref: https://example.test/stage-in.cwl
  workflow:
    $ref: https://example.test/workflow.cwl
  stage_out:
    $ref: https://example.test/stage-out.cwl
"""
    )

    assert loaded["workflows"] == {
        "directory_stage_in": {"class": "CommandLineTool", "id": "stage-in"},
        "workflow": {"class": "Workflow", "id": "workflow"},
        "stage_out": {"class": "CommandLineTool", "id": "stage-out"},
    }


def test_load_url_decompresses_gzip_content():
    mate = ConfigMate()
    response = StubResponse(
        gzip.compress(b'{"compressed": true}'),
        "application/json",
    )
    mate.session.get = Mock(return_value=response)

    assert mate.load_config_from_location("https://example.test/config.gz") == {
        "compressed": True
    }


def test_load_url_rejects_unknown_content_type():
    mate = ConfigMate()
    mate.session.get = Mock(
        return_value=StubResponse(b"value", "application/octet-stream")
    )

    with pytest.raises(ValueError, match="application/octet-stream"):
        mate.load_config_from_location("https://example.test/config")


def test_local_file_is_converted_to_file_url(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("name: local\n")
    mate = ConfigMate()
    original_load = mate.load_config_from_location
    delegated = Mock(return_value={"loaded": True})

    def dispatch(location):
        if location == str(config_file):
            return original_load(location)
        return delegated(location)

    monkeypatch.setattr(mate, "load_config_from_location", dispatch)

    assert mate.load_config_from_location(str(config_file)) == {"loaded": True}
    delegated.assert_called_once_with(config_file.resolve().as_uri())


def test_missing_local_file_is_rejected(tmp_path):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(ValueError, match="resource does not exist"):
        ConfigMate().load_config_from_location(str(missing))
