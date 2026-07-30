# Bundle your first configuration

This tutorial creates two small YAML files and uses Config Mate to collect
them into one deployable file.

## Before you begin

You need Python 3.10 or newer and access to the package registry that provides
Config Mate. Install the package in a virtual environment:

```console
python -m pip install config-mate
config-mate --help
```

## 1. Create a reusable component

Create `components/runtimes.yaml`:

```yaml
python:
  image: python:3.13-slim
  replicas: 2
  healthcheck:
    path: /health
    interval: 30
```

The top-level `python` key gives the component a stable name. Other root
documents can reuse the same value.

## 2. Reference the component

Create `config.yaml` beside the `components` directory:

```yaml
version: 1
services:
  orders:
    runtime:
      $ref: components/runtimes.yaml#/python
    port: 8080
```

The part before `#` locates the document. The fragment `/python` is a JSON
Pointer selecting the `python` key in that document.

Your files now look like this:

```text
.
├── components
│   └── runtimes.yaml
└── config.yaml
```

## 3. Preview the collected configuration

Run:

```console
config-mate config.yaml
```

Because no output path or format was specified, Config Mate writes YAML to
standard output. The collected document includes the component in place of
the reference:

```yaml
version: 1
services:
  orders:
    runtime:
      image: python:3.13-slim
      replicas: 2
      healthcheck:
        path: /health
        interval: 30
    port: 8080
```

## 4. Write a deployable artifact

Create a JSON bundle:

```console
config-mate config.yaml --ext json --output build/config.json
```

Config Mate creates the `build` directory if needed. `build/config.json` is a
single file and no longer requires `components/runtimes.yaml` at runtime.

You have now separated the maintainable source configuration from its
portable delivery artifact.

## Next steps

- [Build a modular configuration](../how-to/modular-configuration.md) covers
  naming, repository layout, reuse, and validation in CI.
- [Use the playground](../how-to/playground.md) lets you experiment with
  references in a browser.
- [CLI reference](../reference/cli.md) documents all formats, transports,
  credentials, and output behavior.
