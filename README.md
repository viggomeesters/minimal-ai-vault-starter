# Minimal AI Vault Starter

Write only daily notes and inbox notes. Deterministic no-LLM automation turns raw bullets into structured JSONL records, AI daily summaries, open loops, entities, decisions, tasks, and searchable context bundles — while never touching your original human notes.

## Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
make check
```

Or, if you already have Python and pytest available:

```bash
make check
```

## Mental model

- `vault/daily/` and `vault/inbox/` are human-owned evidence.
- `records/*.jsonl` plus `schema/*.schema.json` are the canonical structured data layer.
- `views/`, `vault/ai-daily/`, `vault/generated/`, and `dist/` are generated/rebuildable.
- `dist/vaultctx.sqlite` is a runtime projection, not source of truth.
- `docs/*.json` are machine-readable contracts/docs; there are no prose docs you need to read.
- Attachments are referenced by SHA256 metadata and deterministic storage paths.

## Useful commands

```bash
python3 scripts/vaultctx.py validate
python3 scripts/vaultctx.py scan-daily
python3 scripts/vaultctx.py extract --dry-run
python3 scripts/vaultctx.py extract
python3 scripts/vaultctx.py render-views
python3 scripts/vaultctx.py bundle --goal "plan the week"
python3 scripts/vaultctx.py query "weekly planning"
python3 scripts/vaultctx.py build-sqlite
python3 scripts/vaultctx.py hash-attachment vault/attachments/objects/sha256/*/*/weekly-plan-sketch.txt
```

## Attachment contract

Attachment records include `filename`, `media_type`, `size_bytes`, `sha256`, `storage_path`, `source_id`, and `created_at`. Validation checks that each file exists and that size/SHA256 match.

Storage path pattern:

```text
vault/attachments/objects/sha256/<first-two-sha-chars>/<sha256>/<filename>
```

For real personal use, keep private or large attachments local and out of Git unless you intentionally want to share them.

## Privacy boundary

This repo uses synthetic data only: Alex Example, Sam Example, and Example AI Vault Starter. Do not commit real daily notes, exports, screenshots, paths, Telegram ids, API keys, or private attachments to a public starter repo.

## What this is not

This is not a full personal operating system, not a complete Obsidian replacement, and not a cloud memory service. It is a small starter kit showing safe boundaries: human notes as evidence, JSONL as structured truth, generated views as rebuildable UI.
