# Automation model

Recommended jobs:

1. `scan-daily`: read human notes and produce raw events.
2. `extract`: convert raw events to typed records.
3. `render-views`: publish human-readable generated views.
4. `build-sqlite`: build a local runtime query cache.
5. `bundle`: produce bounded, cited context for an AI assistant.

Each job must leave `vault/daily/**` and `vault/inbox/**` untouched.
