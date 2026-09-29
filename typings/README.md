# Local dependency typing

`jsonref.pyi` describes the reference-resolution interface used from
`jsonref==1.1.0`, which does not ship typing metadata. Update it against the
installed implementation when upgrading the dependency. It is configured
through mypy's search path and is not a runtime module.

`jsonref.replace_refs` returns `object` because a reference can resolve to a
scalar, sequence, or mapping. RefBundle checks the resolved root before
returning its documented mapping result.

Session-adapters 0.7.0 supplies its own type metadata; use its upstream types
instead of maintaining local adapter stubs.
