# Config Mate

Config Mate turns a modular JSON, YAML, or XML configuration into a
self-contained document. It starts from one root document, follows its JSON
References (`$ref`), and serializes the collected result as JSON, YAML, or XML.

This lets a team maintain small, reusable configuration components without
giving up compatibility with tools that only accept one file.

## Choose what you need

The documentation is organized around the four
[Diátaxis](https://diataxis.fr/) modes:

| If you want to… | Go to… |
| --- | --- |
| Bundle a small configuration for the first time | [Bundle your first configuration](tutorials/first-bundle.md) |
| Split an existing configuration into reusable components | [Build a modular configuration](how-to/modular-configuration.md) |
| Try `$ref` resolution interactively | [Use the playground](how-to/playground.md) |
| Look up a command, option, environment variable, or exit behavior | [CLI reference](reference/cli.md) |
| Look up supported reference locations and syntax | [`$ref` reference](reference/json-reference.md) |
| Understand why modular configuration matters | [Why modular configuration?](explanation/modular-configuration.md) |
| Understand how the code is organized | [How the implementation is organized](explanation/implementation.md) |

## What Config Mate does

Given a root document like this:

```yaml
service:
  name: orders
  runtime:
    $ref: components/runtimes.yaml#/python
```

Config Mate fetches `components/runtimes.yaml`, selects the `python` value,
recursively resolves any references inside it, and replaces the `$ref` object
with the selected value. The output is a plain, portable document.

References can target:

- another value in the same document;
- a local file;
- an HTTP or HTTPS resource;
- an S3 object; or
- an OCI registry resource.

See the [CLI reference](reference/cli.md#supported-input-locations) for the
transport details and authentication options.

## Where to start

New users should follow [Bundle your first
configuration](tutorials/first-bundle.md). If you already have a large
configuration, read [Why modular
configuration?](explanation/modular-configuration.md) before deciding where
to draw component boundaries.
