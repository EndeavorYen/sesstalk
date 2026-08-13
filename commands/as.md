---
description: Set this session's mailbox name
argument-hint: <this-session-name>
---

# /as

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

Remember `<this-session-name>` as this chat's mailbox.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" as <this-session-name>
```

Print the JSON. Later `/send`, `/reply`, `/handoff`, `/receive`, and `/nudge` use this name as `--from` / inbox.
