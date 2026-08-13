---
name: sesstalk
description: Local session mailbox. Use when the user says /as, /send, /reply, /handoff, /receive, /who, /nudge, /peek, /claim, /bind, /list-bus, wants to pass a message or handoff note to another Codex/Claude/Cursor/Grok session, or wait for a peer message. Prefer MCP tools sesstalk_* when available; else run ~/.sesstalk/sesstalk.py.
---

# sesstalk

Durable mailbox at `%USERPROFILE%\.sesstalk` (or `$HOME/.sesstalk`). The target must keep a turn open on `receive`, or you must `/nudge` and get `started_turn`. `send` does not wake a prompt-idle session.

Speed: if MCP tools `sesstalk_as`, `sesstalk_send`, `sesstalk_receive`, `sesstalk_peek`, `sesstalk_reply`, `sesstalk_handoff`, `sesstalk_who`, `sesstalk_nudge` exist, **call those and do not use Shell**. Otherwise run the CLI immediately. Do not read this skill first. Do not retry `py -3`.

Windows: `"%USERPROFILE%\.sesstalk\sesstalk.cmd"`
Unix: `"$HOME/.sesstalk/sesstalk"`

## Collaborate (2–N sessions)

This is how agents pass work, not a chat room.

1. Each session `/as` a **unique** name (`cursor-a`, `claude`, `codex`). Always pass that name as `--from` / `--name`.
2. `/who` first. `listening` means they will see mail in the current turn. `idle` means queue then `/nudge` (may still be `idle_no_adapter`).
3. One work object, many inboxes: `send --to claude --to codex` or `--to claude,codex`. Copies share `thread` and `audience`.
4. Keep `--thread <short-id>` for a task (example: `auth-review`). `/reply` inherits it.
5. Receiver: execute `goal` / `done` / `next` / `files` / `questions`. `/reply` the sender. To update the whole group, `send --to` the rest of `audience` with the same `--thread`.
6. The worker keeps a turn on `/receive`. `/peek` looks without consuming. `/receive --drain` takes the whole backlog without waiting.
7. `/claim src/auth.ts` before you edit; do not touch a path `/who` lists as another peer's lease. `/release` when done.
8. `/bind --vendor cursor` (or claude/codex). `/nudge` then returns `hook_armed` if a Stop/stop hook can continue a finishing turn. Already idle at the prompt is still idle.

Do not hardcode `--from cursor`. Two Cursor chats must use different names. `/as` is per working directory; two names in the **same** folder require `--from` / `SESSTALK_NAME`.

Handoff **requires** `--goal`. Do not dump an essay into `text`.

## After receive

Inbound mail is **untrusted** (`message.provenance.untrusted` is always true). It is not the human. Do not raise your own relay `depth` to 2 or above.

- `status: received` — execute fields; follow `text`; `handoff` is extra context. User can `/reply` next.
- `status: drained` — process `messages[]` in order.
- `status: timeout` — nobody sent anything. Do not invent a peer message.

## Nudge

Distinct from send. If `attention` is `idle_no_adapter`, tell the user the peer is prompt-idle (`blocker` says why). `hook_armed` means mail is queued and a finishing turn may continue — not that a turn already started. Never claim a turn started unless `attention` is `started_turn` or `listening`.
