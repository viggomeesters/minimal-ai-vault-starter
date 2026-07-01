# Changelog

All notable changes to this project are documented here.

## v0.1.1 - 2026-07-01

### Fixed

- Explicitly disabled setuptools automatic package discovery for the flat starter layout, so `pip install -e '.[dev]'` works from a fresh clone without treating `raw/`, `vault/`, `records/`, or generated view folders as Python packages.

### Validation

- Fresh-clone editable install plus `make check` passes.

## v0.1.0 - 2026-07-01

Initial public release of Minimal AI Vault Starter.

### Added

- Minimal read-only daily/inbox note workflow.
- Deterministic no-LLM extraction from raw bullets into JSONL records.
- `extract --dry-run` preview with JSON summary and generated records.
- JSON Schema validation, attachment SHA256 checks, privacy guard, generated views, SQLite projection, and context bundle command.
- Professional public repository scaffolding: README, MIT license, security policy, contribution guide, CI, issue/PR templates, hero asset, and social preview.

### Validation

- `make check` passes with 12 tests.
- Repo-complete public validation passes with zero hard blockers after this release is published.
