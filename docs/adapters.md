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

No endpoint: `idle_no_adapter` (will not spawn). Connect/RPC fail: `error`. Success: `started_turn` / `adapter: codex_app_server` after `initialize` + `initialized` + matching `turn/start` response id. Layer 1 talks newline JSON-RPC over `tcp://`, JSON-RPC over WebSocket for `unix://` (real Codex app-server protocol, not native Windows), JSON-RPC over `ws://`, **and** the same WebSocket handshake over `ws+unix://PATH` / `unix+ws://PATH`. Fake-peer newline JSON-RPC over UDS uses `jsonl+unix://PATH`. Failures stay `error` / `idle_no_adapter`. Do not start `codex app-server` from nudge. `started_turn` means the app-server accepted `turn/start` after initialize — not a later `turn/started` event.

Portable adapter: `~/.codex/hooks.json` Stop hook → `sesstalk hook --vendor codex` (same JSON as Claude).

### Grok / Hermes

No documented wake API (no Stop hook, no inbox socket, no gateway). Hermes (`~/.hermes` or `$HERMES_HOME`) is a grok-side **host**: the installer copies the skill there, but `nudge --vendor grok` / `hermes` is always `idle_no_adapter`. `bind` / `init` do **not** set `hook: true` for these vendors. Keep `/receive` open. Mail is a drop-box until the peer is blocked on receive.

## Depth

Relay depth still refuses `>= 2`. Hooks inject a continuation that tells the model to `/receive`, not to relay blindly.
