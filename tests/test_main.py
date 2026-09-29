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

import importlib.util
import json
import sys
from base64 import b64decode, b64encode
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import ClassVar, TextIO, TypeAlias

import pytest
from click import UsageError
from click.testing import CliRunner
from session_adapters.conainers_auth import ContainersAuth
from session_adapters.http_conts import ContentType

import ref_bundle.main as main_module
from ref_bundle.main import main

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
def cli_dependencies(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Adapter]:
    """Replace network adapters and configuration loading with recording fakes."""
    for variable in (
        "OCI_HOSTNAME",
        "OCI_USERNAME",
        "OCI_PASSWORD",
        "OAUTH2_BEARER",
        "REGISTRY_AUTH_FILE",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    # Import under the isolated environment so Click captures a safe default path.
    spec = importlib.util.spec_from_file_location("ref_bundle.main", main_module.__file__)
    assert spec is not None and spec.loader is not None
    isolated_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(isolated_main)
    monkeypatch.setattr(sys.modules[__name__], "main_module", isolated_main)
    monkeypatch.setattr(sys.modules[__name__], "main", isolated_main.main)
    FakeConfigMate.instances.clear()
    adapters: dict[str, Adapter] = {}

    def adapter_factory(name: str) -> Callable[..., Adapter]:
        def create(*args: object, **kwargs: object) -> Adapter:
            adapter = (name, args, kwargs)
            adapters[name] = adapter
            return adapter

        return create

    monkeypatch.setattr(main_module, "RefBundle", FakeConfigMate)
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
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.auths is not None
    encoded_auth = containers_auth.auths["registry.test"].auth
    assert encoded_auth is not None
    assert b64decode(encoded_auth).decode() == "user:secret"
    assert cli_dependencies["OCIAdapter"][2] == {}


def test_cli_rejects_an_invalid_extension() -> None:
    result = CliRunner().invoke(main, ["config.yaml", "--ext", "toml"])

    assert result.exit_code == UsageError.exit_code
    assert "Invalid value for '--ext'" in result.output


def test_command_callback_defensively_rejects_unsupported_extension() -> None:
    assert main.callback is not None
    with pytest.raises(ValueError, match="'toml' not supported"):
        main.callback("config.yaml", ext="toml", authfile=None)


def test_cli_exits_with_failure_when_loading_fails(
    cli_dependencies: dict[str, Adapter],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_loading(self: FakeConfigMate, location: str) -> Mapping[str, object]:
        raise ValueError("Configuration could not be loaded")

    monkeypatch.setattr(FakeConfigMate, "load_config_from_location", fail_loading)
    result = CliRunner().invoke(main, ["config.yaml"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert FakeConfigMate.instances[0].dumped is None


@pytest.mark.parametrize(
    ("platform", "runtime_dir", "relative_path"),
    [
        ("linux", "runtime", "runtime/containers/auth.json"),
        ("linux", None, "home/.config/containers/auth.json"),
        ("linux", "", "home/.config/containers/auth.json"),
        ("darwin", "runtime", "home/.config/containers/auth.json"),
        ("win32", "runtime", "home/.config/containers/auth.json"),
    ],
)
def test_default_authfile_selects_platform_path(
    platform: str,
    runtime_dir: str | None,
    relative_path: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    if runtime_dir is None:
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    else:
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / runtime_dir) if runtime_dir else "")

    assert main_module._default_authfile() == tmp_path / relative_path


@pytest.mark.parametrize("source", ["option", "environment", "default"])
def test_cli_loads_authfile_with_option_environment_default_precedence(
    source: str,
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    default_authfile = main_module._default_authfile()
    environment_authfile = tmp_path / "environment.json"
    option_authfile = tmp_path / "option.json"
    for authfile, registry in (
        (default_authfile, "default.test"),
        (environment_authfile, "environment.test"),
        (option_authfile, "option.test"),
    ):
        authfile.parent.mkdir(parents=True, exist_ok=True)
        authfile.write_text(json.dumps({"auths": {registry: {"auth": "dXNlcjpwYXNz"}}}))
    arguments = ["config.yaml"]
    if source in ("option", "environment"):
        monkeypatch.setenv("REGISTRY_AUTH_FILE", str(environment_authfile))
    if source == "option":
        arguments.extend(["--authfile", str(option_authfile)])

    result = CliRunner().invoke(main, arguments)

    assert result.exit_code == 0, result.output
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.auths is not None
    assert set(containers_auth.auths) == {f"{source}.test"}


def test_cli_help_shows_resolved_authfile_default(
    cli_dependencies: dict[str, Adapter],
) -> None:
    default_authfile = main_module._default_authfile()

    result = CliRunner().invoke(main, ["--help"], terminal_width=300)

    assert result.exit_code == 0
    assert f"default: {default_authfile}]" in result.output


def test_cli_keeps_authfile_default_resolved_at_import(
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    default_authfile = main_module._default_authfile()
    default_authfile.parent.mkdir(parents=True, exist_ok=True)
    default_authfile.write_text(json.dumps({"auths": {"default.test": {"auth": "dXNlcjpwYXNz"}}}))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "changed-runtime"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "changed-home")

    result = CliRunner().invoke(main, ["config.yaml"])

    assert result.exit_code == 0, result.output
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.auths is not None
    assert set(containers_auth.auths) == {"default.test"}


@pytest.mark.parametrize("authfile_option", [True, False])
def test_cli_uses_empty_auth_when_authfile_is_missing(
    authfile_option: bool,
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
) -> None:
    arguments = ["config.yaml"]
    if authfile_option:
        arguments.extend(["--authfile", str(tmp_path / "missing.json")])

    result = CliRunner().invoke(main, arguments)

    assert result.exit_code == 0
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.auths == {}


@pytest.mark.parametrize(
    "credentials",
    [
        [],
        ["--oci-hostname", "registry.test"],
        ["--oci-hostname", "registry.test", "--oci-username", "new-user"],
        ["--oci-username", "new-user", "--oci-password", "new-password"],
        ["--oci-hostname", "registry.test", "--oci-password", "new-password"],
    ],
)
def test_cli_preserves_file_credentials_when_explicit_credentials_are_incomplete(
    credentials: list[str],
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
) -> None:
    authfile = tmp_path / "auth.json"
    source = {"auths": {"registry.test": {"auth": "dXNlcjpwYXNz"}}}
    authfile.write_text(json.dumps(source))

    result = CliRunner().invoke(main, ["config.yaml", "--authfile", str(authfile), *credentials])

    assert result.exit_code == 0
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.model_dump(exclude_none=True, by_alias=True) == source


def test_cli_overrides_one_registry_preserving_other_credentials_helpers_and_file(
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
) -> None:
    authfile = tmp_path / "auth.json"
    auths = {
        "registry.test": {"auth": "b2xkOnBhc3M="},
        "other.test": {"auth": "b3RoZXI6cGFzcw=="},
    }
    source = {
        "auths": auths,
        "credHelpers": {"helper.test": "example-helper"},
    }
    original_content = json.dumps(source)
    authfile.write_text(original_content)

    result = CliRunner().invoke(
        main,
        [
            "config.yaml",
            "--authfile",
            str(authfile),
            "--oci-hostname",
            "registry.test",
            "--oci-username",
            "new-user",
            "--oci-password",
            "new:password",
        ],
    )

    assert result.exit_code == 0
    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    auths["registry.test"] = {"auth": b64encode(b"new-user:new:password").decode()}
    assert containers_auth.model_dump(exclude_none=True, by_alias=True) == source
    assert authfile.read_text() == original_content


def test_cli_rejects_invalid_authfile_before_constructing_oci_adapter(
    cli_dependencies: dict[str, Adapter],
    tmp_path: Path,
) -> None:
    authfile = tmp_path / "auth.json"
    authfile.write_text("{invalid")

    result = CliRunner().invoke(main, ["config.yaml", "--authfile", str(authfile)])

    assert result.exit_code == 1
    assert result.exception is not None
    assert "OCIAdapter" not in cli_dependencies
    assert FakeConfigMate.instances[0].loaded_from is None


def test_command_callback_accepts_absent_authfile(cli_dependencies: dict[str, Adapter]) -> None:
    assert main.callback is not None

    main.callback("config.yaml", ext="yaml", authfile=None)

    containers_auth = cli_dependencies["OCIAdapter"][1][0]
    assert isinstance(containers_auth, ContainersAuth)
    assert containers_auth.auths == {}
