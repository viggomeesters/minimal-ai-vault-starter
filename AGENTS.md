# Agent instructions

- Never edit `vault/daily/**` or `vault/inbox/**`.
- Treat those folders as read-only human evidence.
- Canonical structured data lives in `records/*.jsonl` and `schema/*.schema.json`.
- Generated outputs belong in `views/`, `vault/ai-daily/`, `vault/generated/`, and `dist/`.
- Run `make check` before reporting done.
- Use synthetic data only in this public starter.
