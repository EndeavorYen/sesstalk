---
description: Queue a sesstalk message to another named session
argument-hint: <target-name> <text>
---

# /send

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md. Do not list files. Do not retry `py -3`.

This session must already have a name from `/as` or `/receive` in this chat. Remember that name. Always pass it as `--from`.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" send --from <this-chat-name> --to <target-name> <text>
```

Print the JSON. This only queues; it does not wake a prompt-idle session. Use `/nudge` separately if the peer may be idle. Prefer MCP tool `sesstalk_send` when available.
