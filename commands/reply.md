---
description: Reply to the last inbound sesstalk message
argument-hint: <text>
---

# /reply

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

Requires `/as` (or `/receive <name>`) in this chat, plus a prior `/receive` for that same name. All of `$ARGUMENTS` is the reply text.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" reply --from <this-chat-name> <text>
```

This sends to the last inbound `from` with `--reply-to` that message id. Print the JSON.
