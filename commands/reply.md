---
description: Reply to the last inbound sesstalk message
argument-hint: <text>
---

# /reply

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_reply` is available, call it now with `sender` = this chat's `/as` name and `text` = `$ARGUMENTS`. Do not use Shell.

Requires `/as` (or `/receive <name>`) in this chat, plus a prior `/receive` for that same name. All of `$ARGUMENTS` is the reply text. Inherits `thread` from the inbound message.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" reply --from <this-chat-name> <text>
```

This sends to the last inbound `from` with `--reply-to` that message id. Print the JSON.
