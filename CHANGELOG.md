# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - 2026-09-29

### Added

- First public version.
- dynamic resolution of the [authfile](https://man.archlinux.org/man/containers-auth.json.5) according to the requirements below:
    - on Linux, the default is `${XDG_RUNTIME_DIR}/containers/auth.json`;
    - the default value of this option is read from the `REGISTRY_AUTH_FILE` environment variable.

### Changed

- Improved type annotations and internal code quality by addressing mypy, Ruff, and Bandit findings, without changing public APIs or runtime behavior.

[Unreleased]: https://github.com/Terradue/config-mate/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Terradue/config-mate/releases/tag/v1.0.0
