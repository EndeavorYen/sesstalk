# Roadmap

Public plan for sesstalk. GitHub issues are the work items. This file is the north star so we do not grow a chat product by accident.

## Goal

A stranger on one machine can:

1. `python install.py --verify` (or `sesstalk demo`) in under a minute
2. Open two vendor sessions (Cursor, Claude Code, Codex, or Grok)
3. Hand a **structured work object** (`goal` / `next` / `files` / `thread`) across vendors
4. The receiver **starts a turn** or sesstalk **honestly** reports prompt-idle
5. The sender gets a structured reply, fast enough that agents use MCP instead of copy-paste

Not Slack. Not a cloud bus. Not 20 MCP chat tools.

## Done (v0.1–v0.5)

| Slice | What shipped |
|---|---|
| Mailbox | JSONL `send` / `receive` / `reply` / `as`, Windows + Unix |
| Tests + CI | Fake peers, contract, latency, Win/Ubuntu 3.9/3.12 |
| MCP | Optional stdio fast path; CLI remains source of truth |
| Presence | `who`: listening / idle / unknown |
| Work object | `goal` `done` `next` `files` `questions`; handoff requires `--goal` |
| Safety | `provenance.untrusted`, relay depth cap |
| Collab | Fan-out `--to a --to b`, `thread`, `peek`, `drain` |
| Leases | `claim` / `release` so two agents do not edit the same path |
| Attention | Honest nudge; Stop/stop hooks continue a **finishing** turn |
| Demo | `sesstalk demo` + recorded terminal SVG (no LLM) |
| Identity | `/as` keyed by cwd; two chats in one folder must pass `--from` |
| Cursor hook | Stop hook maps cwd → unique bind |
| Claude | Fake AF_UNIX `SendMessage`; native Windows is `idle_no_adapter` |
| Codex | `bind --thread-id` + `--app-server` `tcp://` / `ws://` / `unix://` (not native Windows); never spawn |
| Ops | `version` `schema` `doctor` `init` `log` |
| README | Regenerable zinc+lime SVGs; interop table; explicit **Not this** |

## Milestones

### v1.0 Agents will use it

- [#12](https://github.com/EndeavorYen/sesstalk/issues/12) Epic: close when the README interop table is still true **and** a human records Layer 4 live pairing
- [#22](https://github.com/EndeavorYen/sesstalk/issues/22) Layer 4: one real Cursor + Claude or Codex pairing on the epic (no LLM in CI)

Follow-ups that stay in scope:

- Real Codex `app-server --listen unix://` is WebSocket-over-UDS; Layer 1 `unix://` today is newline JSON-RPC for tests. Document or implement WS-over-UDS without spawning.
- Grok: keep `/receive`; no fake wake API

## Anti-goals (reject PRs)

- Cross-machine / cloud mailbox
- Emoji, channels, “rooms as Slack”
- Pretending Cursor can wake a peer already sitting at the prompt
- Unbounded agent ping-pong (depth cap stays)
- Default-CI LLM calls
- A 20th chat MCP tool (doctor/log/schema are diagnostics)

## How we decide

If a feature does not make **session A hand work to session B faster or more honestly**, it is out of scope — even if it would look good on a star chart.
