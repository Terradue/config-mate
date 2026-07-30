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
from typing import Any, TextIO

from ruamel.yaml import YAML

from . import StreamHandler


class YamlHandler(StreamHandler):
    @staticmethod
    def _create_yaml() -> YAML:
        yaml = YAML(typ="safe")
        yaml.default_flow_style = False
        yaml.representer.ignore_aliases = lambda _data: True
        yaml.representer.sort_base_mapping_type_on_output = False
        return yaml

    def handle(self, stream: TextIO) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        documents = list(self._create_yaml().load_all(stream))

        if len(documents) == 1:
            return documents[0]

        return documents

    def write(
        self, configuration: Mapping[str, Any] | list[Mapping[str, Any]], stream: TextIO
    ):
        yaml = self._create_yaml()
        if isinstance(configuration, list):
            yaml.dump_all(configuration, stream)
        else:
            yaml.dump(configuration, stream)
