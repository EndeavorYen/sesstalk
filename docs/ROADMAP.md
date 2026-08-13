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

## Done (v0.1–v0.4)

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
| README | Interop matrix, demo, explicit **Not this** |

## Milestones

### v0.5 Prove the demo

Strangers must *see* the value without two humans and an LLM.

- [#13](https://github.com/EndeavorYen/sesstalk/issues/13) `sesstalk demo` — done
- [#14](https://github.com/EndeavorYen/sesstalk/issues/14) Recorded terminal demo
- [#15](https://github.com/EndeavorYen/sesstalk/issues/15) CONTRIBUTING + north-star checklist — done

### v0.6 Attention where the host allows

Do not invent wake APIs. Implement or document per vendor.

- [#16](https://github.com/EndeavorYen/sesstalk/issues/16) Hook maps cwd → bound inbox — done
- [#17](https://github.com/EndeavorYen/sesstalk/issues/17) Claude UDS wake (fake socket, skip Windows)
- [#18](https://github.com/EndeavorYen/sesstalk/issues/18) Codex `bind --thread-id` / honest fail

### v1.0 Agents will use it

- [#19](https://github.com/EndeavorYen/sesstalk/issues/19) Two Cursor chats must not clobber `--from`
- [#12](https://github.com/EndeavorYen/sesstalk/issues/12) Epic: close when the milestones above are done and the README interop table is still true

Follow-ups after this loop (do not grow a chat product):

- Codex `ws://` app-server transport (real `--listen`), still never spawn a second agent
- `who` should show per-cwd `/as` names when a folder is ambiguous

## Anti-goals (reject PRs)

- Cross-machine / cloud mailbox
- Emoji, channels, “rooms as Slack”
- Pretending Cursor can wake a peer already sitting at the prompt
- Unbounded agent ping-pong (depth cap stays)
- Default-CI LLM calls

## How we decide

If a feature does not make **session A hand work to session B faster or more honestly**, it is out of scope — even if it would look good on a star chart.
