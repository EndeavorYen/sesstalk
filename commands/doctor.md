---
description: Diagnose sesstalk mailbox, identity, MCP, and hooks
---

# /doctor

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_doctor` is available, call it now. Do not use Shell.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" doctor
```

Print JSON: version, home, cwd identities, binds, whether Cursor/Claude/Codex MCP and hooks mention sesstalk. Read-only. Do not invent a peer message from this output.
