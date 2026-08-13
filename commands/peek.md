---
description: Show the next unread sesstalk message without consuming it
argument-hint: [this-session-name]
---

# /peek

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_peek` is available, call it now with `name` = this session. Do not use Shell.

Otherwise:

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" peek --name <this-session-name>
```

Print unread count and `next`. This does not mark mail read. Use `/receive` to consume.
