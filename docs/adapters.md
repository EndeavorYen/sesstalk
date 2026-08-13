# Attention adapters

Mailbox JSONL stays vendor-neutral. Nudge never writes vendor fields into the queue.

## What nudge may return

| attention | Meaning |
|---|---|
| `listening` | Peer is blocked on `receive` now |
| `started_turn` | An adapter delivered a wake (fake test adapter, or Claude Unix inbox socket) |
| `hook_armed` | `sesstalk bind` (or installer Stop/stop hook). Mail is queued; a **finishing** turn will be continued. Already sitting at the prompt is still idle |
| `idle_no_adapter` | Queued only. See `blocker` |
| `error` | Adapter ran and failed honestly |

## Per vendor

### Cursor

No peer SendMessage. Portable pager is `/receive`.

Real adapter on Windows: `~/.cursor/hooks.json` `stop` hook runs `sesstalk hook --vendor cursor`. If unread mail exists and `status=completed`, it returns `followup_message` (capped by `loop_limit`). Without `--name`, the hook maps the workspace cwd to a unique `bind --cwd` inbox. Two chats in the same folder stay silent (do not guess). `bind --vendor cursor` makes nudge report `hook_armed`.

### Claude Code

Native `SendMessage` / inbox sockets are **macOS and Linux** (Unix domain). Layer 1: `bind --socket` + a fake AF_UNIX server; nudge returns `started_turn` / `adapter: claude_socket`. Native Windows: `idle_no_adapter` (Unix-domain sockets are not the Windows path; use WSL or the Stop hook). Never claim `started_turn` if connect failed.

Portable adapter: Stop hook in `~/.claude/settings.json` → `sesstalk hook --vendor claude` returns `decision: block` once (`stop_hook_active` prevents loops).

### Codex

`turn/start` requires the **live** session `threadId` and a listening app-server. sesstalk does not invent a thread or spawn a second `codex` process.

```text
sesstalk bind --name codex --vendor codex --thread-id thr_... --app-server tcp://127.0.0.1:PORT
sesstalk nudge --name codex --vendor codex
```

No endpoint: `idle_no_adapter` (will not spawn). Connect/RPC fail: `error`. Success: `started_turn` / `adapter: codex_app_server`. Layer 1 talks newline JSON-RPC (`turn/start`). Real Codex `--listen ws://` is a follow-up transport; do not start `codex app-server` from nudge.

Portable adapter: `~/.codex/hooks.json` Stop hook → `sesstalk hook --vendor codex` (same JSON as Claude).

### Grok

No documented wake API. Keep `/receive` open. `blocker` says so.

## Depth

Relay depth still refuses `>= 2`. Hooks inject a continuation that tells the model to `/receive`, not to relay blindly.
