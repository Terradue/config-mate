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

"""Bundle configuration references from the command line."""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from requests.adapters import HTTPAdapter
from session_adapters.bearer_auth_http_adapter import BearerAuthHTTPAdapter
from session_adapters.conainers_auth import ContainersAuth
from session_adapters.file_adapter import FileAdapter
from session_adapters.http_conts import ContentType
from session_adapters.oci_adapter import OCIAdapter
from session_adapters.s3_adapter import S3Adapter

from . import RefBundle


def _default_authfile() -> Path:
    """Resolve the platform default registry credentials path at invocation time."""
    # Windows / macOS
    base_dir = Path.home() / ".config"

    if sys.platform == "linux":
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if runtime_dir:
            base_dir = Path(runtime_dir)

    return base_dir / "containers" / "auth.json"


@click.command()
@click.argument("config", required=True)
@click.option(
    "--ext",
    type=click.Choice(choices=["json", "yaml", "xml"], case_sensitive=False),
    default="yaml",
    help="Specify the bundled configuration serialization.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=False,
    help="The output file path",
)
@click.option("--oci-hostname", envvar="OCI_HOSTNAME", show_envvar=True)
@click.option("--oci-username", envvar="OCI_USERNAME", show_envvar=True)
@click.option("--oci-password", envvar="OCI_PASSWORD", show_envvar=True)
@click.option(
    "--authfile",
    help="Path of the managed registry credentials file",
    envvar="REGISTRY_AUTH_FILE",
    show_envvar=True,
    default=_default_authfile(),
    show_default=True,
    required=False,
    type=click.Path(path_type=Path),
)
@click.option("--oauth2-bearer", envvar="OAUTH2_BEARER", show_envvar=True)
# Click passes each declared option as a separate callback argument.
def main(  # noqa: PLR0913
    config: str,
    *,
    ext: str,
    output: Path | None = None,
    oci_hostname: str | None = None,
    oci_username: str | None = None,
    oci_password: str | None = None,
    authfile: Path | None,
    oauth2_bearer: str | None = None,
) -> None:
    """Resolve CONFIG references and write the selected output format."""
    start_time = time.time()
    exit_code = 0

    logger.info(
        f"Started at: {datetime.fromtimestamp(start_time).isoformat(timespec='milliseconds')}"
    )
    content_type = None

    match ext.lower():
        case "json":
            content_type = ContentType.JSON

        case "yaml":
            content_type = ContentType.YAML

        case "xml":
            content_type = ContentType.XML

        case _:
            raise ValueError(f"'{ext}' not supported (yet), please stay tuned.")

    ref_bundle = _create_ref_bundle(
        oci_hostname, oci_username, oci_password, authfile, oauth2_bearer
    )

    try:
        config_dict = ref_bundle.load_config_from_location(config)

        if output:
            logger.info(f"Saving the new Configuration to {output}...")

            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w") as output_stream:
                ref_bundle.dump_config(
                    configuration=config_dict,
                    stream=output_stream,
                    content_type=content_type,
                )

            logger.info(f"New Configuration successfully saved to {output}!")
        else:
            ref_bundle.dump_config(
                configuration=config_dict, stream=sys.stdout, content_type=content_type
            )

        logger.success("------------------------------------------------------------------------")
        logger.success("SUCCESS")
        logger.success("------------------------------------------------------------------------")
    except Exception as error:
        exit_code = 1
        logger.error("------------------------------------------------------------------------")
        logger.error("FAIL")
        logger.error(error)
        logger.error("------------------------------------------------------------------------")

    end_time = time.time()
    logger.info(f"Total time: {end_time - start_time:.4f} seconds")
    logger.info(
        f"Finished at: {datetime.fromtimestamp(end_time).isoformat(timespec='milliseconds')}"
    )

    if exit_code:
        sys.exit(exit_code)


def _create_ref_bundle(
    oci_hostname: str | None,
    oci_username: str | None,
    oci_password: str | None,
    authfile: Path | None,
    oauth2_bearer: str | None,
) -> RefBundle:
    """Mount the CLI transports with the supplied authentication settings."""
    ref_bundle = RefBundle()

    http_adapter = BearerAuthHTTPAdapter(oauth2_bearer) if oauth2_bearer else HTTPAdapter()
    ref_bundle.mount_session("http://", http_adapter)
    ref_bundle.mount_session("https://", http_adapter)
    ref_bundle.mount_session("file://", FileAdapter())
    ref_bundle.mount_session("s3://", S3Adapter())

    containers_auth = (
        ContainersAuth.get_instance(authfile)
        if authfile is not None and authfile.exists()
        else ContainersAuth(auths={})
    )

    if oci_hostname and oci_username and oci_password:
        containers_auth.add_auth(oci_hostname, oci_username, oci_password)

    ref_bundle.mount_session("oci://", OCIAdapter(containers_auth))

    return ref_bundle
