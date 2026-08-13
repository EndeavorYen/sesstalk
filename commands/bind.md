---
description: Remember this inbox's vendor so nudge can use the Stop/stop hook
argument-hint: <this-session-name> [--vendor cursor|claude|codex|grok]
---

# /bind

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_bind` is available, call it now. Do not use Shell.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" bind --name <this-chat-name> --vendor cursor
"%USERPROFILE%\.sesstalk\sesstalk.cmd" bind --name claude --vendor claude --socket /tmp/claude.sock
"%USERPROFILE%\.sesstalk\sesstalk.cmd" bind --name codex --vendor codex --thread-id thr_... --app-server tcp://127.0.0.1:PORT
```

After bind, `/nudge` reports `hook_armed` instead of pretending a turn started. The peer still needs a Stop/stop hook (installed by `python install.py`) or an open `/receive`.
