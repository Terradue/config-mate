# Build a modular configuration

Use this guide to split a large configuration into generic components and
collect them with `$ref` when producing a delivery artifact.

## Identify reusable concepts

Extract a value when it has a meaning and lifecycle of its own, not merely
because it is large. Good component candidates include:

- runtime or cluster profiles;
- retry, logging, or observability policies;
- workflow templates;
- security policy shapes that do not contain secret values; and
- organization-wide defaults.

Keep environment-specific values, credentials, and one-off application
settings close to the root document. A component is most reusable when its
name describes a capability rather than its first consumer. Prefer
`standard-python-worker` to `orders-worker-settings`.

## Choose a predictable layout

For example:

```text
configuration/
├── roots/
│   ├── development.yaml
│   └── production.yaml
└── components/
    ├── clusters.yaml
    ├── runtimes.yaml
    └── workflows/
        └── stage-in.yaml
```

Treat files under `roots/` as entry points and files under `components/` as
the reusable catalog. Relative references are resolved from the document
that contains the reference, so moving a document can change what its
relative references target.

## Give components stable addresses

A catalog file can expose several named values:

```yaml
# components/runtimes.yaml
python-worker:
  image: python:3.13-slim
  replicas: 2

node-worker:
  image: node:24-slim
  replicas: 2
```

Select one with a JSON Pointer fragment:

```yaml
# roots/production.yaml
services:
  worker:
    runtime:
      $ref: ../components/runtimes.yaml#/python-worker
```

Use document paths and keys as public interfaces. Renaming either is a
breaking change for every root that references it.

## Compose components recursively

Referenced components may contain references of their own. This makes it
possible to build a small hierarchy:

```yaml
# components/services.yaml
worker:
  runtime:
    $ref: runtimes.yaml#/python-worker
  telemetry:
    $ref: policies.yaml#/standard-telemetry
```

```yaml
# roots/production.yaml
services:
  orders:
    $ref: ../components/services.yaml#/worker
```

Keep the hierarchy shallow enough that a reviewer can trace the effective
value. If understanding one service requires following many files, the
component boundaries are too fine-grained.

## Collect and validate the root

Bundle each root document in CI:

```console
config-mate configuration/roots/production.yaml \
  --output build/production.yaml
```

The command exits non-zero if a source cannot be loaded or parsed, a
reference cannot be resolved, or the result cannot be written. This catches
broken paths and pointers before deployment. Validate the collected artifact
with the downstream system's own schema or validation command as a separate
step; Config Mate resolves references but does not enforce an
application-specific schema.

Do not edit files under `build/`. Regenerate them from the modular sources so
that source and artifact cannot drift apart.

## Reference remote catalogs carefully

HTTP, S3, and OCI references let several repositories consume a shared
catalog. Pin remote components to an immutable version, digest, tag policy,
or versioned path whenever the backing system supports it. An unpinned remote
document can change the meaning of an otherwise unchanged root
configuration.

Pass transport credentials through the CLI environment variables rather than
embedding secrets in a `$ref`. See [Remote inputs and
authentication](../reference/cli.md#remote-inputs-and-authentication).
