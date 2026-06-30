# Daily note contract

```yaml
human_owned:
  - vault/daily/**
  - vault/inbox/**

agent_owned:
  - raw/**
  - records/**
  - views/**
  - vault/ai-daily/**
  - vault/generated/**
  - dist/**

daily_notes:
  ai_permissions:
    read: true
    quote_with_source: true
    derive_records: true
    create_generated_views: true
    edit_original: false
    add_links_to_original: false
    reformat_original: false
    append_to_original: false
```

The validation workflow captures hashes for human-owned demo notes and fails if automation changes them.
