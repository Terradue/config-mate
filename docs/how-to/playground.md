# Use the playground

The Config Mate playground is a Streamlit application for experimenting with
YAML and seeing its fully resolved form immediately. It is useful for learning
`$ref`, reviewing a configuration fragment, and diagnosing a reference before
adding it to a root document.

The playground is an exploration tool. Use the CLI for repeatable builds and
CI pipelines.

## Resolve the included example

1. Start the application using one of the methods below.
2. Open the URL printed by Streamlit, or `http://localhost` for the container
   tasks.
3. Review or edit the YAML in the code editor.
4. Select **Update**.
5. Read the **Referenced and parsed configuration** below the editor.

A green **Success** badge means the YAML was parsed and all references were
resolved. A **Validation failure** badge includes the parser, loading, or
reference error.

The bundled example demonstrates both internal references such as
`#/components/recipes/simple_exit_handler` and HTTPS references to remote CWL
documents. The machine running Streamlit must be able to reach any remote
resource used by the example.

## Run your working tree in a container

To build the playground from the current checkout and run it:

```console
task run_playground_dev
```

This is the most representative option when changing Config Mate or the
playground itself.

## Run the application directly

From the repository root, install the application dependencies and start
Streamlit:

```console
python -m pip install -e .
python -m pip install streamlit streamlit-code-editor
streamlit run playground/playground.py
```

Streamlit normally serves the application at `http://localhost:8501`.

## Understand the playground's limits

- The editor accepts YAML input and displays YAML output.
- The playground does not save a bundle to disk; copy the result or reproduce
  the operation with the CLI.
- It is not an application-schema validator. Success means the document was
  parsed and its references were resolved.
- Remote references are fetched by the Streamlit server, not by the browser.
- Do not paste secrets into a shared or remotely hosted playground.

For command-line output formats and authenticated remote references, use the
[CLI](../reference/cli.md).
