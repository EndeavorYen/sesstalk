---
description: Send a handoff note or file to another named session
argument-hint: <target-name> <file-or-note>
---

# /handoff

User arguments: $ARGUMENTS

Run immediately. Do not read SKILL.md.

Remember this chat's mailbox name from `/as`. Always pass `--from`. First token is `<target-name>`. The rest is either an existing file path, or an inline note.

If the next token is an existing file:

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" handoff --from <this-chat-name> --to <target-name> --file <path> [optional text]
```

Otherwise treat the rest as an inline note:

```text
"%USERPROFILE%\.sesstalk\sesstalk.cmd" handoff --from <this-chat-name> --to <target-name> --note "<note>"
```

Print the JSON. Receiver should treat `message.handoff` as the sender's working note.
