# CLI reference

`config-mate` loads one root configuration, recursively resolves its `$ref`
values, and serializes the collected document.

## Synopsis

```text
config-mate [OPTIONS] CONFIG
```

```console
config-mate --help
config-mate config.yaml
config-mate config.yaml --output build/config.yaml
config-mate config.yaml --ext json --output build/config.json
```

`CONFIG` is required. It can be a local path or a supported URI.

## Options

| Option | Value | Default | Description |
| --- | --- | --- | --- |
| `--ext` | `json`, `yaml`, or `xml` | `yaml` | Serialization format of the collected output. The match is case-insensitive. |
| `--output` | path | standard output | Write to a file. Missing parent directories are created and an existing file is overwritten. |
| `--oci-hostname` | text | `OCI_HOSTNAME` | Hostname used by the OCI transport adapter. |
| `--oci-username` | text | `OCI_USERNAME` | Username used by the OCI transport adapter. |
| `--oci-password` | text | `OCI_PASSWORD` | Password used by the OCI transport adapter. |
| `--oauth2-bearer` | text | `OAUTH2_BEARER` | Bearer token sent for HTTP and HTTPS requests. |
| `--help` | — | — | Show command help and exit. |

The output format is controlled by `--ext`, not by the extension in
`--output`. For example, this command writes JSON despite the `.txt` suffix:

```console
config-mate config.yaml --ext json --output build/config.txt
```

## Standard output and logs

Without `--output`, the collected document is written to standard output.
Operational logs are emitted separately, so the data can be redirected or
piped:

```console
config-mate config.yaml --ext json > build/config.json
```

Prefer `--output` when the command itself should create missing parent
directories:

```console
config-mate config.yaml --output build/nested/config.yaml
```

## Supported input locations

The root `CONFIG` and external `$ref` values can use the transports mounted by
the CLI:

| Location | Example | Notes |
| --- | --- | --- |
| Local path | `config/root.yaml` | Converted internally to an absolute `file://` URI. |
| File URI | `file:///workspace/config/root.yaml` | Must use a valid file URI. |
| HTTP(S) | `https://example.org/config/root.yaml` | Optional bearer authentication is applied to both HTTP and HTTPS. |
| S3 | `s3://configuration/root.yaml` | Uses the S3 session adapter and its credential discovery behavior. |
| OCI | `oci://registry.example.org/team/root.yaml` | Uses the OCI options or their environment-variable equivalents. |

Input may be YAML, JSON, or XML. For remote inputs, the response
`Content-Type` selects the parser; when that header is absent, Config Mate
assumes YAML. Gzip-compressed response bodies are detected and decompressed.

See the [`$ref` reference](json-reference.md) for fragments and relative
resolution.

## Remote inputs and authentication

### HTTP bearer token

Pass a token as an option:

```console
config-mate https://config.example.org/root.yaml \
  --oauth2-bearer "$CONFIG_TOKEN"
```

Or expose it through the supported environment variable:

```console
export OAUTH2_BEARER="$CONFIG_TOKEN"
config-mate https://config.example.org/root.yaml
```

The same HTTP adapter is used when following HTTP or HTTPS references inside
the root document.

### OCI credentials

Pass credentials directly:

```console
config-mate oci://registry.example.org/team/root.yaml \
  --oci-hostname registry.example.org \
  --oci-username "$OCI_USER" \
  --oci-password "$OCI_PASS"
```

Or use environment variables:

```console
export OCI_HOSTNAME=registry.example.org
export OCI_USERNAME="$OCI_USER"
export OCI_PASSWORD="$OCI_PASS"
config-mate oci://registry.example.org/team/root.yaml
```

Environment variables keep credentials out of shell history, but they are
still visible to processes with access to the environment. Use the secret
facility provided by your CI system.

## Output formats

The input and output formats are independent. A YAML root can be collected as
JSON or XML:

```console
config-mate config.yaml --ext json --output build/config.json
config-mate config.yaml --ext xml --output build/config.xml
```

YAML is the default:

```console
config-mate config.json --output build/config.yaml
```

## Exit behavior

The command exits with:

- `0` after successful resolution and serialization;
- `1` when loading, parsing, resolving, or writing fails; and
- Click's non-zero usage exit when arguments or option values are invalid.

Failures are logged with a **FAIL** marker and the underlying exception.
Success is logged with a **SUCCESS** marker. Do not treat a partially created
output file as valid after a failure; only consume the artifact when the
command exits successfully.
