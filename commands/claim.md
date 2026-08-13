---
description: Claim a file path so another sesstalk session does not edit it
argument-hint: <path> [--ttl seconds]
---

# /claim

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_claim` is available, call it with `sender` = this chat's `/as` name and `path` = `$ARGUMENTS`. Do not use Shell.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" claim --from <this-chat-name> --path <path> --ttl 600
```

Conflict means another peer holds the lease. Do not edit that path. `/release` when done.
