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

import sys
import time
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from requests.adapters import HTTPAdapter
from session_adapters.bearer_auth_http_adapter import BearerAuthHTTPAdapter
from session_adapters.file_adapter import FileAdapter
from session_adapters.http_conts import ContentType
from session_adapters.oci_adapter import OCIAdapter
from session_adapters.s3_adapter import S3Adapter

from . import ConfigMate


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
@click.option("--oauth2-bearer", envvar="OAUTH2_BEARER", show_envvar=True)
def main(
    config: str,
    ext: str,
    output: Path | None = None,
    oci_hostname: str | None = None,
    oci_username: str | None = None,
    oci_password: str | None = None,
    oauth2_bearer: str | None = None,
):
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

    config_mate = ConfigMate()

    http_adapter = (
        BearerAuthHTTPAdapter(oauth2_bearer) if oauth2_bearer else HTTPAdapter()
    )
    config_mate.mount_session("http://", http_adapter)
    config_mate.mount_session("https://", http_adapter)
    config_mate.mount_session("file://", FileAdapter())
    config_mate.mount_session("s3://", S3Adapter())
    config_mate.mount_session(
        "oci://",
        OCIAdapter(hostname=oci_hostname, username=oci_username, password=oci_password),
    )

    try:
        config_dict = config_mate.load_config_from_location(config)

        if output:
            logger.info(f"Saving the new Configuration to {output}...")

            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w") as output_stream:
                config_mate.dump_config(
                    configuration=config_dict,
                    stream=output_stream,
                    content_type=content_type,
                )

            logger.info(f"New Configuration successfully saved to {output}!")
        else:
            config_mate.dump_config(
                configuration=config_dict, stream=sys.stdout, content_type=content_type
            )

        logger.success(
            "------------------------------------------------------------------------"
        )
        logger.success("SUCCESS")
        logger.success(
            "------------------------------------------------------------------------"
        )
    except Exception as e:
        exit_code = 1
        logger.error(
            "------------------------------------------------------------------------"
        )
        logger.error("FAIL")
        logger.error(e)
        logger.error(
            "------------------------------------------------------------------------"
        )

    end_time = time.time()
    logger.info(f"Total time: {end_time - start_time:.4f} seconds")
    logger.info(
        f"Finished at: {datetime.fromtimestamp(end_time).isoformat(timespec='milliseconds')}"
    )

    if exit_code:
        sys.exit(exit_code)
