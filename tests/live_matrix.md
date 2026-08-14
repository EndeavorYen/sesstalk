# Layer 4 live vendor matrix (opt-in)

Default CI does not run this. Use it after a host-specific adapter change.

Same machine, two named sessions. Record pass/fail and a corpus fixture under `tests/corpus/` if something breaks.

| from \ to | Cursor | Claude | Codex | Grok |
|---|---|---|---|---|
| Cursor | | | | |
| Claude | | | | |
| Codex | | | | |
| Grok | | | | |

Grok/Hermes cells stay queue-only: keep `/receive` open. `nudge --vendor grok` is `idle_no_adapter`. Do not record a fake wake.

Checks per cell:

1. `/as` unique names
2. send-first then receive
3. receive-first then send
4. handoff `--goal` round-trip
5. `/who` shows `listening` during receive
7. Fan-out `--to a --to b` shares `thread`
8. `/peek` does not consume; `--drain` empties a backlog
9. `/claim` conflict; Stop/stop hook followup when unread (see `docs/pairing.md`)
