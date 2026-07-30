# Why modular configuration?

Large configuration files tend to accumulate three different kinds of
information: reusable policy, application-specific intent, and
environment-specific values. When they live in one document, repetition hides
which settings are intentional and makes a change difficult to propagate
safely.

Config Mate supports a source-and-artifact model:

```text
small root documents ─┐
generic components ───┼─ $ref resolution ─> one collected artifact
remote catalogs ──────┘
```

Humans maintain the modular sources. Systems that require a single file
consume the collected artifact.

## Reuse is more than removing duplication

A generic component gives a configuration concept a name and a clear owner.
For example, `standard-python-worker` can capture an approved image,
healthcheck, and resource profile. Root documents then express the meaningful
choice—use the standard worker—instead of copying its implementation details.

This has several effects:

- **Consistency:** consumers begin from the same reviewed policy.
- **Change control:** a component can be updated and tested in one place.
- **Review clarity:** root-document diffs show application intent rather than
  repeated boilerplate.
- **Discoverability:** a component catalog exposes supported building blocks.
- **Earlier failure:** collecting roots in CI catches missing resources and
  invalid pointers before the runtime system sees them.

The goal is not the fewest possible lines. The goal is a useful boundary
between stable, generic capabilities and local decisions.

## `$ref` is the assembly mechanism

JSON Reference provides a URI-shaped address for a component. URI resolution
makes the same composition model useful across a file tree, a web server, an
S3 bucket, or an OCI registry. JSON Pointer fragments allow one catalog
document to publish several values.

Because the model is understood by specifications such as JSON Schema and
OpenAPI and by many editors, authors can work with familiar syntax. Config
Mate fills the delivery gap for consumers that cannot load a multi-document
configuration: it follows the references and produces one self-contained
snapshot.

## A component catalog is an API

Once several roots use `components/runtimes.yaml#/python-worker`, the document
path and pointer are an interface. Component maintainers should apply the same
discipline used for a software API:

- choose capability-oriented names;
- document the value's intended use and assumptions;
- preserve compatible paths and shapes;
- version breaking changes; and
- test representative consumers before publishing.

Remote catalogs increase organizational reuse, but also increase coupling.
Pinning a version makes collection reproducible and prevents a component
publisher from silently changing a consumer's next artifact.

## Collection defines a trust boundary

Collecting a configuration fetches and incorporates referenced content.
Therefore every referenced file, host, bucket, or registry becomes part of
the configuration's supply chain.

Use authenticated transports where needed, restrict references to trusted
locations, and avoid putting credentials in source documents. Review the
collected artifact when adopting a new remote component. Config Mate resolves
content; it does not establish that the content is trustworthy or valid for a
particular application.

## The trade-offs

Modularity introduces indirection. Excessively small components make a
configuration hard to read, while mutable remote references can make a build
hard to reproduce. Collection also creates a generated artifact that must not
be edited independently.

A practical design keeps cohesive settings together, uses a shallow
composition hierarchy, pins shared remote content, and regenerates artifacts
in automation. Keep a value local until a stable reusable concept emerges;
extracting every repeated scalar usually creates more navigation than value.

For an actionable workflow, see [Build a modular
configuration](../how-to/modular-configuration.md).
