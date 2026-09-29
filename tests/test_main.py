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

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import ClassVar, TextIO, TypeAlias

import pytest
from click import UsageError
from click.testing import CliRunner
from session_adapters.http_conts import ContentType

from config_mate.main import main

Adapter: TypeAlias = tuple[str, tuple[object, ...], dict[str, object]]


class FakeConfigMate:
    """Record CLI transport registration and configuration rendering."""

    instances: ClassVar[list["FakeConfigMate"]] = []

    def __init__(self) -> None:
        self.mounts: list[tuple[str, Adapter]] = []
        self.loaded_from: str | None = None
        self.dumped: tuple[Mapping[str, object], ContentType] | None = None
        self.__class__.instances.append(self)

    def mount_session(self, scheme: str, adapter: Adapter) -> None:
        """Record the transport mounted for a URL prefix."""
        self.mounts.append((scheme, adapter))

    def load_config_from_location(self, location: str) -> Mapping[str, object]:
        """Record the input location and return a sample configuration."""
        self.loaded_from = location
        return {"loaded": location}

    def dump_config(
        self, configuration: Mapping[str, object], stream: TextIO, content_type: ContentType
    ) -> None:
        """Record the output format and write sample output."""
        self.dumped = (configuration, content_type)
        stream.write("rendered")


@pytest.fixture
def cli_dependencies(monkeypatch: pytest.MonkeyPatch) -> dict[str, Adapter]:
    """Replace network adapters and configuration loading with recording fakes."""
    import config_mate.main as main_module

    FakeConfigMate.instances.clear()
    adapters: dict[str, Adapter] = {}

    def adapter_factory(name: str) -> Callable[..., Adapter]:
        def create(*args: object, **kwargs: object) -> Adapter:
            adapter = (name, args, kwargs)
            adapters[name] = adapter
            return adapter

        return create

    monkeypatch.setattr(main_module, "ConfigMate", FakeConfigMate)
    for name in (
        "HTTPAdapter",
        "BearerAuthHTTPAdapter",
        "FileAdapter",
        "S3Adapter",
        "OCIAdapter",
    ):
        monkeypatch.setattr(main_module, name, adapter_factory(name))

    return adapters


def test_cli_renders_to_stdout_and_mounts_default_adapters(
    cli_dependencies: dict[str, Adapter],
) -> None:
    result = CliRunner().invoke(main, ["config.yaml", "--ext", "json"])

    assert result.exit_code == 0
    assert result.stdout == "rendered"
    mate = FakeConfigMate.instances[0]
    assert mate.loaded_from == "config.yaml"
    assert mate.dumped == ({"loaded": "config.yaml"}, ContentType.JSON)
    assert [scheme for scheme, _adapter in mate.mounts] == [
        "http://",
        "https://",
        "file://",
        "s3://",
        "oci://",
    ]
    assert mate.mounts[0][1] is mate.mounts[1][1]
    assert mate.mounts[0][1][0] == "HTTPAdapter"


def test_cli_uses_yaml_output_by_default(cli_dependencies: dict[str, Adapter]) -> None:
    result = CliRunner().invoke(main, ["config.yaml"])

    assert result.exit_code == 0
    assert FakeConfigMate.instances[0].dumped == (
        {"loaded": "config.yaml"},
        ContentType.YAML,
    )


def test_cli_writes_output_and_configures_credentials(
    tmp_path: Path, cli_dependencies: dict[str, Adapter]
) -> None:
    output = tmp_path / "nested" / "config.xml"
    result = CliRunner().invoke(
        main,
        [
            "remote.yaml",
            "--ext",
            "XML",
            "--output",
            str(output),
            "--oauth2-bearer",
            "token",
            "--oci-hostname",
            "registry.test",
            "--oci-username",
            "user",
            "--oci-password",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert output.read_text() == "rendered"
    mate = FakeConfigMate.instances[0]
    assert mate.dumped == ({"loaded": "remote.yaml"}, ContentType.XML)
    assert cli_dependencies["BearerAuthHTTPAdapter"][1] == ("token",)
    assert cli_dependencies["OCIAdapter"][2] == {
        "hostname": "registry.test",
        "username": "user",
        "password": "secret",
    }


def test_cli_rejects_an_invalid_extension() -> None:
    result = CliRunner().invoke(main, ["config.yaml", "--ext", "toml"])

    assert result.exit_code == UsageError.exit_code
    assert "Invalid value for '--ext'" in result.output


def test_command_callback_defensively_rejects_unsupported_extension() -> None:
    assert main.callback is not None
    with pytest.raises(ValueError, match="'toml' not supported"):
        main.callback("config.yaml", ext="toml")
