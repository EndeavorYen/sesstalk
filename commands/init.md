---
description: Name this chat and bind its vendor in one step
argument-hint: <this-session-name> [--vendor cursor|claude|codex|grok]
---

# /init

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" init --name <this-chat-name> --vendor cursor
```

This is `/as` plus `/bind`. Later commands still pass `--from` / `--name`. Two chats in the same folder must keep unique names.
