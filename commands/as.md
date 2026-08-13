---
description: Set this session's mailbox name
argument-hint: <this-session-name>
---

# /as

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_as` is available, call it now with `name` = `$ARGUMENTS`. Do not use Shell.

Remember `<this-session-name>` as this chat's mailbox. Always pass it as `--from` / `--name` later. Two chats in the same folder share `~/.sesstalk`; a global identity file must not pick the other window.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" as <this-session-name>
```

Print the JSON. Later `/send`, `/reply`, `/handoff`, `/receive`, and `/nudge` use this name as `--from` / inbox.
