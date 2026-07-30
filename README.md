# Config Mate

[![PyPI - Version](https://img.shields.io/pypi/v/config-mate.svg)](https://pypi.org/project/config-mate)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/config-mate.svg)](https://pypi.org/project/config-mate)

Transpiler Mate is a Python library and CLI that extracts `schema.org/SoftwareApplication` metadata from annotated CWL documents and converts it into publication-ready formats.

Config Mate recursively resolves JSON References (`$ref`) across JSON, YAML,
and XML configuration and writes one self-contained JSON, YAML, or XML
artifact.

```console
config-mate config/root.yaml --output build/config.yaml
```

Maintaining reusable policy, runtime profiles, workflows, and other generic
configuration as named components keeps root documents focused on application
intent. Config Mate collects those modular sources for downstream tools that
only accept a single file.

## Documentation

The documentation follows the [Diátaxis](https://diataxis.fr/) structure:

- [Tutorial: bundle your first configuration](docs/tutorials/first-bundle.md)
- [How to build a modular configuration](docs/how-to/modular-configuration.md)
- [How to use the playground](docs/how-to/playground.md)
- [CLI reference](docs/reference/cli.md)
- [`$ref` reference](docs/reference/json-reference.md)
- [Explanation: why modular configuration?](docs/explanation/modular-configuration.md)
- [Explanation: how the implementation is organized](docs/explanation/implementation.md)

## Install

Config Mate requires Python 3.10 or newer. After configuring access to the
package registry used by your organization:

```console
python -m pip install config-mate
config-mate --help
```

### Hatch projects

To add Config Mate to a named Hatch environment, configure the package index
and dependency in `pyproject.toml`:

```toml
[tool.hatch.envs.prod.env-vars]
PIP_EXTRA_INDEX_URL = "https://token:{env:TOKEN_PYPI_REGISTRY}@git.terradue.com/api/v4/projects/{env:PYPI_PROJECT_ID}/packages/pypi/simple/"

[tool.hatch.envs.prod]
path = "/app/envs/my-hatch-env"
dependencies = [
  "config-mate",
]
```

If Config Mate is a runtime dependency of the package itself rather than a
development environment, declare it under `[project]` instead:

```toml
[project]
dependencies = [
  "config-mate",
]
```

## Quick example

Given `components/runtimes.yaml`:

```yaml
python:
  image: python:3.13-slim
  replicas: 2
```

and `config.yaml`:

```yaml
service:
  runtime:
    $ref: components/runtimes.yaml#/python
```

run:

```console
config-mate config.yaml --ext json --output build/config.json
```

The output is a single JSON document with the referenced runtime inlined.

## Playground

The Streamlit playground provides an editor for trying YAML references and
viewing the resolved result:

```console
task run_playground
```

See [Use the playground](docs/how-to/playground.md) for published-container,
development-container, and direct-run instructions.

### Local quality checks

Install [Hatch](https://hatch.pypa.io/) and [Taskfiles](https://taskfile.dev/docs/guide) then install the Git hook:

```console
task quality:pre-commit:install
```

Every commit runs Ruff (including the configured McCabe complexity limit),
Ruff formatting, strict mypy checks, and the pytest suite.
Run the complete hook explicitly with:

```console
task quality:pre-commit:run

## License

[![Apache License, Version 2.0](https://img.shields.io/badge/license-Apache%20License%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
