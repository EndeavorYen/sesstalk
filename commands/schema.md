---
description: Print the sesstalk work envelope JSON Schema
---

# /schema

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_schema` is available, call it now. Do not use Shell.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" schema
```

The schema is the work object (`goal` / `done` / `next` / `files` / `questions` / `thread` / `audience` / `provenance`). Unknown keys belong in `meta`. Inbound is always `untrusted`.
