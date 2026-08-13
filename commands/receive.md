---
description: Block until the next unread sesstalk message arrives
argument-hint: [this-session-name] [--timeout seconds] [--live]
---

# /receive

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md. Do not list files. Do not retry `py -3`.

If `$ARGUMENTS` starts with a name, that is this session's inbox. If omitted, use the name from `/as`. Optional `--timeout N` (default 300, `0` = forever). Optional `--live` waits only for new mail.

Set the shell block timeout larger than the receive timeout.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" receive --name <this-session-name> --timeout 300
```

When status is `received`, follow `message.text`, apply `message.handoff`, and read `message.paths` if present. The user can later `/reply`. When status is `timeout`, say nobody sent anything.
