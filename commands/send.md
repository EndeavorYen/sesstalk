---
description: Queue a sesstalk message to one or more named sessions
argument-hint: <target[,target...]> <text>
---

# /send

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md. Do not list files. Do not retry `py -3`.

If MCP tool `sesstalk_send` is available, call it now (do not use Shell):
- `sender` = this chat's `/as` name
- `to` = first token (comma-separated peers allowed, e.g. `claude,codex`)
- `text` = the rest
- optional `thread` if the user named a task

Otherwise Shell:

This session must already have a name from `/as`. Always pass it as `--from`. First token is `<target-name>` or `a,b`. Repeat `--to` for extra peers.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" send --from <this-chat-name> --to <target-name> <text>
```

Print the JSON. This only queues; it does not wake a prompt-idle session. Use `/nudge` separately if the peer may be idle.
