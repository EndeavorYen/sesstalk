---
description: Best-effort wake a named session; does not replace /send
argument-hint: <name> [--vendor cursor|claude|codex|grok]
---

# /nudge

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

If MCP tool `sesstalk_nudge` is available, call it now. Do not use Shell.

This is not `/send`. Mail must already be queued or will still need `/send`. Nudge only tries to start a turn.

If the peer is already `/receive`-ing, you will get `attention: listening`. If no adapter exists, you will get `attention: idle_no_adapter` — tell the user the message is queued but the peer is prompt-idle.

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" nudge --name <peer> --vendor cursor
```

Unix also accepts a positional peer: `sesstalk nudge hermes --vendor grok`. Grok/Hermes return `idle_no_adapter`; keep `/receive` open.
