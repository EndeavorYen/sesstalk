---
description: Show which sessions are listening, idle, or unknown
---

# /who

Run immediately. Do not read SKILL.md.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" who
```

Print name, state (`listening` / `idle` / `unknown`), unread count, and last activity. `listening` means a `receive` is in progress now. Prefer MCP tool `sesstalk_who` when available.
