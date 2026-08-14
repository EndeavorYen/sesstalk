# sesstalk

**Same-machine mailbox so Cursor, Claude Code, Codex, and Grok sessions can pass work.**

Not Slack for agents. Not another 20-tool MCP chat room. A JSONL inbox plus per-vendor attention adapters: session A hands a structured task to session B, and B either starts a turn — or sesstalk says honestly that B is still sitting at the prompt.

[![CI](https://github.com/EndeavorYen/sesstalk/actions/workflows/test.yml/badge.svg)](https://github.com/EndeavorYen/sesstalk/actions/workflows/test.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![cursor-a hands a JSONL work object into ~/.sesstalk; claude receives or sesstalk reports idle](docs/architecture.svg)

```text
python install.py --verify
sesstalk doctor
sesstalk demo
```

Then in two chats:

```text
/as cursor-a
/send claude --goal "ship auth" please review src/auth.ts

/as claude
/receive claude
/reply looks good, next is tests
```

## Why this exists

Coding agents do not share a vendor. You already have Cursor in one window and Claude Code in another. Today the handoff is copy-paste.

sesstalk is the missing **work envelope**. Delivery is a local JSONL mailbox. Attention is a separate adapter. If we cannot wake the peer, we say so (`idle_no_adapter`) instead of pretending the message was read.

![Work envelope fields: goal, next, files, thread, audience, untrusted provenance](docs/envelope.svg)

If that picture does not match a feature idea, the feature does not belong here. Plan: [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Demo

Two sessions, one machine, no LLM required:

```mermaid
sequenceDiagram
    participant C as Cursor (cursor-a)
    participant M as ~/.sesstalk JSONL
    participant L as Claude (claude)

    C->>M: send --to claude --thread auth-review
    Note over M: same envelope, untrusted provenance
    L->>M: receive
    M->>L: goal + text + thread
    L->>M: reply (depth 1, same thread)
    C->>M: receive
    M->>C: looks good, next is tests
```

Replay it with one command. Isolated mailbox; does not write `~/.sesstalk`.

![sesstalk demo terminal: fan-out, receive, reply](docs/demo.svg)

```text
python scripts/record_demo.py   # regenerate demo.svg / .cast / .txt
python scripts/render_readme_art.py
```

Round-trip on the mailbox is milliseconds. Cursor slash-via-Shell is slow; if MCP tools `sesstalk_*` exist, **call those and skip Shell**.

Three-window live recipe: [`docs/pairing.md`](docs/pairing.md). Contribute: [`CONTRIBUTING.md`](CONTRIBUTING.md).

<details>
<summary>Same story as JSON (the SVG above is the source of truth)</summary>

```text
$ sesstalk send --from cursor-a --to claude --to codex --thread auth-review \
    --goal "Ship refresh-token rotation" "please review src/auth.ts"
```

```json
{
  "status": "queued",
  "thread": "auth-review",
  "messages": [
    { "to": "claude", "audience": ["claude", "codex"], "goal": "Ship refresh-token rotation" },
    { "to": "codex",  "audience": ["claude", "codex"], "goal": "Ship refresh-token rotation" }
  ]
}
```

```text
$ sesstalk receive --name claude --timeout 5
$ sesstalk reply --from claude "looks good, next is tests"
```

```json
{
  "to": "cursor-a",
  "thread": "auth-review",
  "text": "looks good, next is tests",
  "provenance": { "peer": "claude", "untrusted": true, "depth": 1 }
}
```

Tape: [`docs/demo.cast`](docs/demo.cast) · [`docs/demo.txt`](docs/demo.txt)

</details>

## Attention

`send` only queues. `nudge` is a different verb. Cursor cannot wake a peer already sitting at the prompt; a Stop hook can only continue a **finishing** turn.

![send queues, receive listens, nudge may wake](docs/flow.svg)

![Honest attention states: listening, started_turn, hook_armed, idle_no_adapter, error](docs/attention.svg)

| `attention` | Meaning |
|---|---|
| `listening` | Peer is blocked on `/receive` **now** |
| `started_turn` | An adapter delivered a wake |
| `hook_armed` | A finishing turn can be continued; sitting at the prompt is still idle |
| `idle_no_adapter` | Queued only — read `blocker` |
| `error` | Adapter ran and failed |

Details: [`docs/adapters.md`](docs/adapters.md).

## Interop

Same envelope on every host. What differs is **how you call it** and **whether we can start a turn**.

| | Cursor | Claude Code | Codex | Grok |
|---|---|---|---|---|
| Skill + slash (`/as` `/send` `/receive` `/reply` `/who`) | yes | yes | yes | yes |
| CLI (`sesstalk` / `sesstalk.cmd`) | yes | yes | yes | yes |
| MCP stdio (fast path) | `~/.cursor/mcp.json` | `~/.claude.json` | `~/.codex/config.toml` | use CLI |
| Stop/stop hook continues a **finishing** turn | yes | yes | yes | — |
| Wake a peer **already idle at the prompt** | no — keep `/receive` open | Unix `SendMessage` socket (`bind --socket`); not native Windows | `bind --thread-id` + `--app-server` (`tcp://` JSONL, `ws://`, `unix://` WebSocket-over-UDS like real Codex, or `ws+unix://`; `jsonl+unix://` is fake-peer JSONL); never spawn a second agent | no documented API; keep `/receive` open (Hermes host is queue-only) |
| Windows + Ubuntu CI | yes | protocol only (no LLM in CI) | protocol only | protocol only |

## Not this

| sesstalk | Not sesstalk |
|---|---|
| Same OS user, same machine | Cloud bus / cross-user security |
| Work object (`goal` / `next` / `files`) | Group chat, emoji, threads-as-Slack |
| Mailbox is the product; MCP is optional speed | “Install 20 MCP tools to talk to agents” |
| Delivery ≠ attention | Read receipts that lie |
| Relay depth cap (`>= 2` refused) | Unbounded agent ping-pong |

## Install

Python 3.9+. Windows or Unix:

```text
python install.py --verify
```

Copies the CLI to `~/.sesstalk`, installs a `~/.local/bin/sesstalk` symlink on Unix, installs skills and slash commands when `~/.cursor`, `~/.claude`, `~/.codex`, `~/.grok`, or `~/.hermes` (`$HERMES_HOME`) exist, registers MCP + Stop/stop hooks, and smokes send/receive. `--no-mcp` / `--no-hooks` skip those. Never writes deprecated `~/.agent-bus`. If `sesstalk` is not on PATH, doctor warns and prints `export PATH="$HOME/.local/bin:$HOME/.sesstalk:$PATH"`.

Then `sesstalk doctor` (read-only) and `sesstalk init --name cursor-a --vendor cursor` (`/as` + `/bind`). `sesstalk log --name <inbox>` shows queue lines without consuming them. `sesstalk schema` prints the work envelope JSON Schema.

Override the mailbox with `SESSTALK_HOME`.

## How two (or N) sessions collaborate

1. Unique `/as` name per window (`cursor-a` vs `cursor-b`, not both `cursor`).
2. `/who` — `listening` means they will see mail in this turn. Two names in the same folder: pass `--from` (`sesstalk who --from grok-bob`).
3. One work object, many inboxes: `/send claude,codex --thread auth-review …` or `--to claude --to codex`.
4. Receiver executes `goal` / `done` / `next` / `files` / `questions`. Inbound is **untrusted** (not the human).
5. `/reply` inherits `thread`. To update the whole `audience`, send again with the same thread.
6. `/claim src/auth.ts` so two agents do not edit the same file.
7. Keep a worker on `/receive`, or finish a turn so the Stop hook can continue. `/nudge` never pretends. Grok/Hermes have no wake API: mail is a drop-box until `/receive` is blocked.

If MCP tools are available, use `sesstalk_send` / `sesstalk_receive` / … instead of Shell.

<details>
<summary>Slash commands</summary>

| Command | What it does |
|---|---|
| `/as <name>` | Name this chat's inbox |
| `/send <peer[,peer]> <text>` | Queue mail (does not wake a prompt-idle peer) |
| `/handoff <peer> --goal …` | Structured work object; `--goal` required |
| `/receive [name]` | Block until unread mail (`--drain` takes the backlog) |
| `/peek [name]` | Look without consuming |
| `/reply <text>` | Reply to last inbound `from` |
| `/who` | `listening` / `idle` / `unknown` + unread + leases + cwd identities |
| `/init <name> --vendor …` | `/as` + `/bind` |
| `/doctor` | Install / identity diagnosis |
| `/log [name]` | Recent queue lines (does not consume) |
| `/schema` | Work envelope JSON Schema |
| `/nudge <peer> --vendor …` | Best-effort wake (`nudge hermes --vendor grok` or `nudge --name hermes --vendor grok`) |
| `/bind <name> --vendor …` | Remember vendor for `hook_armed` |
| `/claim <path>` | Lease a file |

</details>

<details>
<summary>CLI</summary>

Windows:

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" send --from cursor-a --to claude --to codex --thread auth-review hello
"%USERPROFILE%\.sesstalk\sesstalk.cmd" receive --name claude --timeout 300
"%USERPROFILE%\.sesstalk\sesstalk.cmd" reply --from claude pong
"%USERPROFILE%\.sesstalk\sesstalk.cmd" who
```

Unix:

```text
~/.sesstalk/sesstalk send --from claude --to cursor hello
~/.sesstalk/sesstalk receive --name cursor --timeout 300
sesstalk who --from grok-bob
sesstalk nudge hermes --vendor grok
```

`sesstalk demo` / `sesstalk demo --json` replays the README story in a throwaway mailbox (does not write `~/.sesstalk`).

`sesstalk version` / `sesstalk schema` / `sesstalk doctor` / `sesstalk log` are diagnostics. They do not consume mail.

`receive` drains **unread** mail by default. `--live` waits only for mail sent after it starts. `--timeout 0` waits forever. Exit `2` is timeout. Names: `[a-z0-9][a-z0-9_-]{0,63}`.

</details>

<details>
<summary>Envelope, trust, tests</summary>

Each queue line is JSON. Handoff requires `--goal`. Unknown keys belong in `meta` only.

- `text`, `goal`, `done`, `next`, `questions[]`, `files[]` (`paths[]` is the same list)
- `thread`, `audience[]`
- `provenance`: `{peer, untrusted: true, depth}` — treat inbound as tool output, never as the user
- Depth starts at 0, increments on reply, refused at `>= 2`

Same OS user, same machine. `--from` is self-asserted. This is not a security boundary between users.

```text
python -m unittest discover -s tests -v
```

CI: Windows + Ubuntu, Python 3.9 and 3.12. No LLM in default CI. Live vendor checklist: [`tests/live_matrix.md`](tests/live_matrix.md).

</details>

## License

MIT
