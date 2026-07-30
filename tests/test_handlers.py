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

import json
from io import StringIO

import pytest
from ruamel.yaml import YAML

from config_mate.handlers.json_handler import JsonHandler
from config_mate.handlers.xml_handler import XmlHandler
from config_mate.handlers.yaml_handler import YamlHandler


def test_json_handler_reads_and_writes_configuration():
    handler = JsonHandler()
    configuration = {"service": {"enabled": True}, "ports": [80, 443]}

    assert handler.handle(StringIO(json.dumps(configuration))) == configuration

    output = StringIO()
    handler.write(configuration, output)
    assert json.loads(output.getvalue()) == configuration


def test_json_handler_rejects_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        JsonHandler().handle(StringIO("{invalid"))


def test_yaml_handler_reads_all_documents():
    stream = StringIO("name: first\n---\nname: second\n")

    assert YamlHandler().handle(stream) == [
        {"name": "first"},
        {"name": "second"},
    ]


def test_yaml_handler_does_not_wrap_a_single_document_in_a_list():
    stream = StringIO("name: single\n")

    assert YamlHandler().handle(stream) == {"name": "single"}


@pytest.mark.parametrize(
    "configuration",
    [
        {"name": "single", "enabled": True},
        [{"name": "first"}, {"name": "second"}],
    ],
)
def test_yaml_handler_writes_single_and_multiple_documents(configuration):
    output = StringIO()

    YamlHandler().write(configuration, output)

    documents = list(YAML(typ="safe").load_all(output.getvalue()))
    expected = configuration if isinstance(configuration, list) else [configuration]
    assert documents == expected


def test_yaml_handler_does_not_serialize_shared_values_as_anchors_and_aliases():
    shared = {"retries": 3}
    configuration = {"defaults": shared, "services": [shared, shared]}
    output = StringIO()

    YamlHandler().write(configuration, output)

    rendered = output.getvalue()
    assert "&id" not in rendered
    assert "*id" not in rendered
    assert list(YAML(typ="safe").load_all(rendered)) == [configuration]


def test_yaml_handler_preserves_mapping_key_order():
    configuration = {
        "z-top": 1,
        "a-top": {
            "z-nested": 2,
            "a-nested": 3,
        },
    }
    output = StringIO()

    YamlHandler().write(configuration, output)

    rendered = output.getvalue()
    assert rendered.index("z-top") < rendered.index("a-top")
    assert rendered.index("z-nested") < rendered.index("a-nested")


def test_xml_handler_reads_document():
    configuration = XmlHandler().handle(
        StringIO("<service><name>api</name><port>8080</port></service>")
    )

    assert configuration == {"service": {"name": "api", "port": "8080"}}


def test_xml_handler_writes_configuration_document():
    output = StringIO()

    XmlHandler().write({"service": {"name": "api"}}, output)

    rendered = output.getvalue()
    assert rendered.startswith('<?xml version="1.0" encoding="utf-8"?>')
    assert XmlHandler().handle(StringIO(rendered)) == {
        "configuration": {"service": {"name": "api"}}
    }
