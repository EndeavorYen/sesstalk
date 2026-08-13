# Live pairing: three sessions, one machine

Opt-in. Default CI does not run this. Goal: prove Cursor + another vendor can share a `thread`.

## Setup

From the sesstalk clone:

```text
python install.py --verify
```

Open three chats (mix vendors if you can). Unique names:

```text
/init cursor-a --vendor cursor
/init claude --vendor claude
/init codex --vendor codex
```

(/init is /as + /bind. Unique names still required.)

Keep at least one worker on `/receive` **or** finish a turn so the Stop/stop hook can continue.

## Script

1. From cursor-a: `/who`
2. `/send claude,codex --thread pairing-1 please reply with your name`
3. `/nudge claude --vendor claude` then `/nudge codex --vendor codex`
4. Expected attention: `listening`, `hook_armed`, `started_turn`, or honest `idle_no_adapter` / `error`
5. Receivers: execute the text, `/reply pong from <name>`
6. cursor-a `/receive --drain` — both pongs, same `thread` on the outbound copies
7. `/claim src/auth.ts` on cursor-a; claude `/claim src/auth.ts` should fail
8. Record the vendor pair on GitHub issue [#12](https://github.com/EndeavorYen/sesstalk/issues/12)

## Failures

Add `tests/corpus/issue-N-short-name.json` and a unittest replay. Do not put LLM calls in default CI.
