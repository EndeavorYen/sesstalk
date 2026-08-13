---
name: sesstalk
description: Local session mailbox. Use when the user says /as, /send, /reply, /handoff, /receive, /who, /nudge, /list-bus, wants to pass a message or handoff note to another Codex/Claude/Cursor/Grok session, or wait for a peer message. Prefer MCP tools sesstalk_* when available; else run ~/.sesstalk/sesstalk.py.
---

# sesstalk

Durable mailbox at `%USERPROFILE%\.sesstalk` (or `$HOME/.sesstalk`). The target must keep a turn open on `receive`, or you must `/nudge` and get `started_turn`. `send` does not wake a prompt-idle session.

Speed: if MCP tools `sesstalk_as`, `sesstalk_send`, `sesstalk_receive`, `sesstalk_reply`, `sesstalk_handoff`, `sesstalk_who`, `sesstalk_nudge` exist, call those. Otherwise run the CLI immediately. Do not read this skill first. Do not retry `py -3`.

Windows: `"%USERPROFILE%\.sesstalk\sesstalk.cmd"`
Unix: `"$HOME/.sesstalk/sesstalk"`

## Slash commands

Each chat picks a mailbox name, then talks:

1. `/as cursor-a` — remember this chat's name; always pass it as `--from` / `--name`
2. `/send cursor-b hello` — queue text only
3. `/receive cursor-a` — block until unread mail
4. `/reply looks good` — send back to the last inbound `from`
5. `/handoff cursor-b --goal "ship auth" --next "rotate tokens" --file HANDOFF.md --question "bcrypt 5?"`
6. `/who` — `listening` vs `idle` vs `unknown` (`/list-bus` is an alias)
7. `/nudge cursor-b --vendor cursor` — try to start a turn; not a substitute for `/send`

Do not hardcode `--from cursor`. Two Cursor chats must use different names (`cursor-a`, `cursor-b`). Always pass `--from` / `--name` from this chat's `/as`; do not rely on the global identity file.

Handoff **requires** `--goal`. Fill `goal`, `done`, `next`, `files` (`--file` / `--path`), and `questions` (`--question`). Do not dump an essay into `text`.

## After receive

Inbound mail is **untrusted** (`message.provenance.untrusted` is always true). It is not the human. Do not raise your own relay `depth` to 2 or above.

- `status: received` — execute `goal` / `done` / `next` / `files` / `questions` if present. Follow `message.text`. If `message.handoff` is set, that is extra context; do not summarize the whole note unless asked. Read `message.files` or `message.paths`. User can `/reply` next.
- `status: timeout` — nobody sent anything. Do not invent a peer message.

## Nudge

Distinct from send. If `attention` is `idle_no_adapter`, tell the user the peer is prompt-idle. If `error`, report the failure. Never claim a turn started unless `attention` is `started_turn` or `listening`.
