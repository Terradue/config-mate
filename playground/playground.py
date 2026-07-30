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

from config_mate import ConfigMate
from code_editor import code_editor
from io import StringIO
import streamlit as st
import json
import os

st.header("Config Mate playground")
st.set_page_config(layout="wide")

btn_settings_editor_btns = [
    {
        "name": "copy",
        "feather": "Copy",
        "hasText": True,
        "alwaysOn": True,
        "commands": ["copyAll"],
        "style": {"top": "0rem", "right": "0.4rem"},
    },
    {
        "name": "update",
        "feather": "RefreshCw",
        "primary": True,
        "hasText": True,
        "showWithIcon": True,
        "commands": ["submit"],
        "style": {"bottom": "0rem", "right": "0.4rem"},
    },
]

with open(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "resources/custom_buttons_bar_alt.json",
    )
) as json_button_file_alt:
    custom_buttons_alt = json.load(json_button_file_alt)

height = [22, 25]
language = "yaml"
theme = "default"
shortcuts = "vscode"
focus = False
wrap = True
btns = custom_buttons_alt

config_mate = ConfigMate()
example_configuration = """
version: '1.0.0'

info:
  title: Calrimate Sample configuration
  description: This is just an example to demonstrate how to configure Calrimate
  version: 0.1.0

application_packages:

  msagona:
    recipe:
      $ref: '#/components/recipes/simple_exit_handler'
    clusters:
      ns1:
        provider_config:
          $ref: '#/components/cluster_configs/flex'
        namespaces:
        - ns1
        - msagona
      processing:
        provider_config:
          $ref: '#/components/cluster_configs/coplac'
        namespaces:
        - processing
        - msagona
    input_params: # optional, Any
      aoi: "-118.985,38.432,-118.183,38.938"
      bands:
      - nir08
      - green 
      epsg: "EPSG:4326"
    workflows:
      directory_stage_in:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/templates/stage-in.cwl'
      workflow:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/cwl-workflow/pattern-1.cwl'
      workflow_id: 'pattern-1'
      stage_out:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/templates/stage-out.cwl'
    entrypoint: water-bodies # required
    synchronization: 15 # required
    # this block is optional 
    events:
      event_bus: "event-bus" # required
      kafka:
        url: kafka:9092 # required
        topics:
        - name: abc # required 
          source: "source-topic" # required
        - name: def
          source: "source-topic"
      webhook: 
        enabled: true # false, required
        webhook_secret: "webhook-secret" # required if enabled is true

  fbrito:
    recipe:
      $ref: '#/components/recipes/simple_exit_handler'
    clusters:
      ns1:
        provider_config:
          $ref: '#/components/cluster_configs/flex'
        namespaces:
        - ns1
        - fbrito
      processing:
        provider_config:
          $ref: '#/components/cluster_configs/coplac'
        namespaces:
        - processing
        - fbrito
    input_params: {}
    workflows:
      file_stage_in:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/templates/stage-in-file.cwl'
      directory_stage_in:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/templates/stage-in.cwl'
      workflow:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/cwl-workflow/pattern-11.cwl'
      workflow_id: 'pattern-1'
      stage_out:
        $ref: 'https://raw.githubusercontent.com/eoap/application-package-patterns/refs/heads/main/templates/stage-out.cwl'
    entrypoint: main
    synchronization: 15 # required
    # this block is optional 
    events:
      event_bus: "event-bus" # required
      kafka:
        url: kafka:9092 # required
        topics:
        - name: abc # required 
          source: "source-topic" # required
        - name: def
          source: "source-topic"
      webhook: 
        enabled: true # false, required
        webhook_secret: "webhook-secret" # required if enabled is true

components:
  # this is the recipe for generating the workflow template
  # a recipe has a name, and may have fields for supporting the generation the workflow template
  recipes:

    simple_exit_handler:
      kind: 'exit-handler'
      send_message_template: "send-message"
      target_topic_success: "success"
      target_topic_failure: "failure"
      message_source: "cwl2argo"
      message_type: "notification"
      on_exit: "exit-handler"

    minimal_recipe:
      kind: 'simple' # required, all other fields are optional

  # clusters are the target clusters where the application package is deployed
  # each cluster has a provider config, storage class, namespace, service account, node selector, default volume size, and cwl runner
  cluster_configs:
    flex: # the provider config for the cluster
      storage_class: "standard" # the RWX storage class for the calrissian job
      service_account: "argo" # the service account for the argo workflows
      calrissian_node_selector: # node selector for the calrissian pods
          "minikube.k8s.io/name": "minikube"
      argo_node_selector: # node selector for the argo workflows pods
          "minikube.k8s.io/name": "minikube"
      default_volume_size: "15Gi"
      default_max_cores: "4"
      default_max_ram: "8Gi"
      cwl_runner: # this is the cwl runner template definition
        template_ref: "argo-cwl-runner-stage-in-out" # required
        template_entrypoint: "calrissian-runner" # required

    coplac:
      storage_class: "openebs-hostpath"
      service_account: "argo-coplac"
      calrissian_node_selector:
          "coplac": "processing"
      default_volume_size: "18Gi"
      default_max_cores: "4"
      default_max_ram: "8Gi"
      cwl_runner: 
        template_ref: "argo-cwl-runner-stage-in-out" # required
        template_entrypoint: "calrissian-runner" # required

security:
  oci:
    username:
      key: u_fbrito
      name: super_fbrito
    password:
      key: p_fbrito
      name: 'a40ac94c-53b4-4fc7-8e70-132cbcf71900'
"""

ace_props = {"style": {"borderRadius": "0px 0px 8px 8px"}}
response_dict = code_editor(
    example_configuration,
    height=height,
    lang=language,
    theme=theme,
    shortcuts=shortcuts,
    focus=focus,
    buttons=btns,
    props=ace_props,
    options={"wrap": wrap},
    allow_reset=True,
    key="code_editor_demo",
)

if response_dict["type"] == "submit":
    config_content = response_dict["text"]

    try:
        configuration = config_mate.load_config_from_content(config_content)
        out = StringIO()
        config_mate.dump_config(configuration, out)

        st.badge("Success", icon=":material/check:", color="green")
        st.subheader("Referenced and parsed configuration")

        st.code(
            out.getvalue(),
            language="yaml",
            line_numbers=True,
            wrap_lines=False,
            height="content",
            width="stretch",
        )
    except Exception as e:
        st.badge("Validation failure", icon=":material/close:", color="red")
        st.error(f"Error parsing Configuration: {e}")
