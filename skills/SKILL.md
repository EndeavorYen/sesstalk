---
name: sesstalk
description: Local session mailbox. Use when the user says /as, /send, /reply, /handoff, /receive, /who, /list-bus, wants to pass a message or handoff note to another Codex/Claude/Cursor/Grok session, or wait for a peer message. Runs ~/.sesstalk/sesstalk.py.
---

# sesstalk

Durable mailbox at `%USERPROFILE%\.sesstalk` (or `$HOME/.sesstalk`). The target must keep a turn open on `receive`. This does not wake a prompt-idle session.

Speed: run the CLI immediately. Do not read this skill first. Do not retry `py -3`.

Windows: `"%USERPROFILE%\.sesstalk\sesstalk.cmd"`
Unix: `"$HOME/.sesstalk/sesstalk"`

## Slash commands

Each chat picks a mailbox name, then talks:

1. `/as cursor-a` — remember this chat's name; always pass it as `--from` / `--name`
2. `/send cursor-b hello` — queue text
3. `/receive cursor-a` — block until unread mail
4. `/reply looks good` — send back to the last inbound `from`
5. `/handoff cursor-b HANDOFF.md` or `/handoff cursor-b still on auth, next is tests`
6. `/who` — list inboxes (`/list-bus` is an alias)

Do not hardcode `--from cursor`. Two Cursor chats must use different names (`cursor-a`, `cursor-b`). Always pass `--from` / `--name` from this chat's `/as`; do not rely on the global identity file.

## After receive

- `status: received` — follow `message.text`; if `message.handoff` is set, that is the sender's working note; if `message.paths` is set, read those files. User can `/reply` next.
- `status: timeout` — nobody sent anything. Do not invent a peer message.
