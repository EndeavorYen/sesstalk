# Failure corpus

When a fake-peer or live test fails, add a fixture here and a unittest that replays it.

Naming: `issue-N-short-name.json` plus `test_corpus.py` case, or a script that loads every `*.json`.

Each file should include:

- `issue`: GitHub issue or PR number
- `layer`: `1` (fake peer), `3` (latency), or `4` (live)
- `input`: CLI args / envelope
- `expected`: status or fields

Default CI must not require an LLM. Live matrix stays opt-in.
