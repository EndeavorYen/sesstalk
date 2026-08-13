# sesstalk

Local mailbox so **Cursor, Claude Code, Codex, and Grok sessions can talk to each other**.

Same machine. Same slash commands. No cloud. No MCP required.

This is a durable inbox, not Slack and not a pager. The receiving session must keep a turn open on `/receive`. sesstalk does **not** wake a session that has already returned to the prompt.

## Install

Python 3.9+. From this repo:

```text
python install.py
```

That copies the CLI to `~/.sesstalk` (or `%USERPROFILE%\.sesstalk`) and installs skills plus slash commands for Cursor, Claude Code, Codex, and Grok when those folders exist.

Override the mailbox directory with `SESSTALK_HOME`.

## Slash commands

Each chat picks a name, then talks:

```text
/as cursor-a
/send cursor-b please review auth
/handoff cursor-b C:\repo\HANDOFF.md
/receive cursor-a
/reply lgtm, tests next
/who
```

| Command | What it does |
|---|---|
| `/as <name>` | Name this chat's inbox |
| `/send <peer> <text>` | Queue a message |
| `/handoff <peer> <file-or-note>` | Pass a working note or file |
| `/receive [name]` | Block until the next unread message |
| `/reply <text>` | Reply to the last inbound sender |
| `/who` | List inboxes (`/list-bus` is an alias) |

Two Cursor chats need two names (`cursor-a`, `cursor-b`). Always pass `--from` / `--name` from this chat's `/as`.

## CLI

Windows:

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" as cursor-a
"%USERPROFILE%\.sesstalk\sesstalk.cmd" send --from cursor-a --to cursor-b hello
"%USERPROFILE%\.sesstalk\sesstalk.cmd" receive --name cursor-b --timeout 300
"%USERPROFILE%\.sesstalk\sesstalk.cmd" reply --from cursor-b pong
"%USERPROFILE%\.sesstalk\sesstalk.cmd" handoff --from cursor-a --to cursor-b --note "next is tests"
"%USERPROFILE%\.sesstalk\sesstalk.cmd" list
```

Unix:

```text
~/.sesstalk/sesstalk send --from claude --to cursor hello
~/.sesstalk/sesstalk receive --name cursor --timeout 300
```

`receive` reads **unread** mail by default (send-first still works). `--live` waits only for messages sent after receive starts; a timeout does not discard unread mail. `--timeout 0` waits forever. Exit `2` is timeout.

Names: `[a-z0-9][a-z0-9_-]{0,63}`.

## Envelope

Each queued line is JSON:

- `text` — short instruction
- `handoff` — working note (inline `--note` or `--file`, max 200KB)
- `paths[]` — filesystem paths for the peer to read
- `meta` — `KEY=VALUE`
- `from` / `to` / `reply_to` / `id` / `ts`

## Status

Phase 1: portable mailbox + slash commands on Windows and Unix.

Not yet: waking a prompt-idle session. That needs a per-vendor adapter (Claude `SendMessage`, Codex `turn/start`, Cursor sidecar). Delivery is not attention.

## License

MIT
