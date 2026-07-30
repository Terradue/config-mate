# `$ref` reference

Config Mate recognizes JSON Reference objects in JSON, YAML, and XML-derived
data. A reference object contains a `$ref` whose value is a URI reference:

```yaml
runtime:
  $ref: components/runtimes.yaml#/python
```

The URI has two useful parts:

```text
components/runtimes.yaml # /python
└──── document URI ────┘   └ JSON Pointer fragment
```

The document URI locates a resource. The optional fragment selects a value
inside that resource.

## Reference forms

| Form | Example | Meaning |
| --- | --- | --- |
| Same document | `#/definitions/worker` | Select a value from the current document. |
| Whole adjacent document | `worker.yaml` | Use the entire document. |
| Value in adjacent document | `worker.yaml#/runtime` | Select `runtime` from an adjacent document. |
| Parent directory | `../shared.yaml#/logging` | Resolve the path relative to the current document. |
| File URI | `file:///workspace/shared.yaml#/logging` | Load an absolute local file URI. |
| HTTP(S) URI | `https://example.org/shared.yaml#/logging` | Load a remote document. |
| S3 URI | `s3://configuration/shared.yaml#/logging` | Load through the S3 adapter. |
| OCI URI | `oci://registry.example.org/team/shared.yaml#/logging` | Load through the OCI adapter. |

Relative references are resolved against the URI of the document containing
the `$ref`, including when that document was itself referenced.

## JSON Pointer fragments

A fragment beginning with `/` walks through object keys:

```yaml
components:
  policies:
    retry:
      attempts: 3

service:
  retry:
    $ref: "#/components/policies/retry"
```

The reference resolves to:

```yaml
attempts: 3
```

JSON Pointer escapes `~` as `~0` and `/` as `~1` inside a key. For example,
the key `application/json` is selected with:

```yaml
$ref: "#/content/application~1json"
```

## Resolution behavior

- References are resolved recursively.
- Resolved values are emitted as ordinary values rather than `$ref` proxy
  objects.
- Config Mate merges sibling properties beside `$ref` into a referenced
  mapping. This is a non-standard extension and other JSON Reference tools
  may ignore those siblings. Prefer a separately named component when the
  source must remain portable.
- The output is a collected snapshot. It no longer tracks later changes to
  referenced documents.

For the rationale and design trade-offs, read [Why modular
configuration?](../explanation/modular-configuration.md).
