# Contributing

sesstalk is a same-machine mailbox so Cursor, Claude Code, Codex, and Grok sessions can pass **work**. It is not Slack for agents.

## North star

A change belongs here only if it makes this sentence more true:

> Session A on vendor X hands a structured task to session B on vendor Y; B starts a turn **or** sesstalk reports honestly that B is prompt-idle; A gets a structured reply; the round-trip is fast enough that agents use MCP instead of copy-paste.

If a PR cannot check that box, it is out of scope — even if it would look good on a star chart.

Plan and issue numbers: [`docs/ROADMAP.md`](docs/ROADMAP.md). Open or claim a GitHub issue before a large change.

## PR checklist

Copy this into the pull request (the template asks the same questions):

- [ ] Makes A→B **faster** or **more honest** (not a chat-room feature)
- [ ] Does **not** add cloud / cross-user / cross-machine delivery
- [ ] Does **not** pretend a vendor can wake a peer already sitting at the prompt
- [ ] Does **not** raise the relay depth cap or add unbounded ping-pong
- [ ] Default CI still has **no LLM**
- [ ] Layer 1 fake-peer tests: `python -m unittest discover -s tests -v`
- [ ] README interop table still true, or the PR updates the cell that would otherwise lie

## Local loop

```text
python -m unittest discover -s tests -v
python install.py --verify
sesstalk demo
python scripts/render_readme_art.py
python scripts/record_demo.py
```

Windows: `"%USERPROFILE%\.sesstalk\sesstalk.cmd" demo`

Code, comments, README, and issue text are English. Envelope fields stay `goal` / `done` / `next` / `files` / `questions` / `thread`.

## What we reject

| Reject | Why |
|---|---|
| Rooms, emoji, Slack-like UI | Wrong product |
| Cloud bus | Wrong threat model; same OS user only |
| Fake `started_turn` | Honesty is the product |
| LLM in default CI | Tests must be fake peers |
| Second Codex/Cursor agent as a “wake” | Never spawn a peer to deliver mail |

## Layers

1. Fake peers (`tests/`) — required
2. (reserved)
3. Latency (`tests/test_latency.py`) — included in the same unittest command
4. Live vendors — optional; describe the pair in the PR. Checklist: [`tests/live_matrix.md`](tests/live_matrix.md)
