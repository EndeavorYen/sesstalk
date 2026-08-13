#!/usr/bin/env python3
"""sesstalk: local JSONL mailbox so coding sessions can talk to each other."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def bus_home() -> Path:
    for key in ("SESSTALK_HOME", "AGENT_BUS_HOME"):
        override = os.environ.get(key)
        if override:
            return Path(override).expanduser()
    return Path.home() / ".sesstalk"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def die(message: str, code: int = 1) -> None:
    print(json.dumps({"ok": False, "error": message}), flush=True)
    raise SystemExit(code)


def normalize_name(raw: str) -> str:
    name = raw.strip().lower()
    if not NAME_RE.match(name):
        die("name must match [a-z0-9][a-z0-9_-]{0,63}")
    return name


def ensure_dirs(home: Path) -> None:
    (home / "queues").mkdir(parents=True, exist_ok=True)
    (home / "cursors").mkdir(parents=True, exist_ok=True)


class ExclusiveLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fd: int | None = None

    def __enter__(self) -> ExclusiveLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + 10
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode("utf-8"))
                return self
            except FileExistsError:
                if time.time() > deadline:
                    die(f"could not lock {self.path}")
                time.sleep(0.05)

    def __exit__(self, *_exc: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def sessions_path(home: Path) -> Path:
    return home / "sessions.json"


def load_sessions(home: Path) -> dict[str, Any]:
    path = sessions_path(home)
    if not path.exists():
        return {"sessions": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sessions": {}}


def save_sessions(home: Path, data: dict[str, Any]) -> None:
    path = sessions_path(home)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def register_session(home: Path, name: str) -> None:
    with ExclusiveLock(home / "sessions.lock"):
        data = load_sessions(home)
        sessions = data.setdefault("sessions", {})
        sessions[name] = {
            "name": name,
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "updated_at": now_iso(),
        }
        save_sessions(home, data)


def queue_path(home: Path, name: str) -> Path:
    return home / "queues" / f"{name}.jsonl"


def cursor_path(home: Path, name: str) -> Path:
    return home / "cursors" / f"{name}.offset"


def read_offset(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return max(0, int(path.read_text(encoding="utf-8").strip() or "0"))
    except ValueError:
        return 0


def write_offset(path: Path, offset: int) -> None:
    path.write_text(str(offset), encoding="utf-8")


def state_path(home: Path) -> Path:
    return home / "state.json"


def load_state(home: Path) -> dict[str, Any]:
    path = state_path(home)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_state(home: Path, data: dict[str, Any]) -> None:
    path = state_path(home)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def identity_name(home: Path, explicit: str | None) -> str:
    if explicit:
        return normalize_name(explicit)
    for key in ("SESSTALK_NAME", "AGENT_BUS_NAME"):
        env = os.environ.get(key, "").strip()
        if env:
            return normalize_name(env)
    stored = str(load_state(home).get("identity") or "").strip()
    if stored:
        return normalize_name(stored)
    return ""


def set_identity(home: Path, name: str) -> None:
    data = load_state(home)
    data["identity"] = name
    save_state(home, data)


def last_inbound_path(home: Path, name: str) -> Path:
    return home / "last" / f"{name}.json"


def remember_inbound(home: Path, inbox: str, message: dict[str, Any]) -> None:
    path = last_inbound_path(home, inbox)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(message, indent=2) + "\n", encoding="utf-8")
    data = load_state(home)
    if not data.get("identity"):
        data["identity"] = inbox
    data["last_inbox"] = inbox
    save_state(home, data)


def load_last_inbound(home: Path, inbox: str) -> dict[str, Any] | None:
    path = last_inbound_path(home, inbox)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def queue_message(
    home: Path,
    *,
    sender: str,
    target: str,
    text: str,
    reply_to: str | None,
    handoff: str | None,
    paths: list[str],
    meta: dict[str, str],
) -> dict[str, Any]:
    if not text and not handoff and not paths:
        die("message text, --note, --handoff, or --path is required")
    payload = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "from": sender,
        "to": target,
        "reply_to": reply_to,
        "text": text,
        "handoff": handoff,
        "paths": paths,
        "meta": meta,
    }
    append_message(home, payload)
    return payload


def append_message(home: Path, payload: dict[str, Any]) -> None:
    target = payload["to"]
    qpath = queue_path(home, target)
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    with ExclusiveLock(home / "queues" / f"{target}.lock"):
        with qpath.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())


def load_handoff(path_value: str | None) -> str | None:
    if not path_value:
        return None
    path = Path(path_value).expanduser()
    if not path.is_file():
        die(f"handoff file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if len(text) > 200_000:
        die("handoff file is larger than 200KB; pass a path in --path instead")
    return text


def parse_meta(items: list[str] | None) -> dict[str, str]:
    meta: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            die("--meta must be KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            die("--meta key is empty")
        meta[key] = value
    return meta


def cmd_send(args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    sender = identity_name(home, args.sender) or "anonymous"
    target = normalize_name(args.to)
    text = (args.text or "").strip()
    notes: list[str] = []
    if args.note:
        notes.append(args.note)
    file_note = load_handoff(args.handoff)
    if file_note:
        notes.append(file_note)
    handoff = "\n\n".join(notes) if notes else None
    paths = [str(Path(item).expanduser()) for item in (args.path or [])]
    meta = parse_meta(args.meta)
    payload = queue_message(
        home,
        sender=sender,
        target=target,
        text=text,
        reply_to=args.reply_to,
        handoff=handoff,
        paths=paths,
        meta=meta,
    )
    print(json.dumps({"ok": True, "status": "queued", "message": payload}), flush=True)


def cmd_as(args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    name = normalize_name(args.name)
    set_identity(home, name)
    print(json.dumps({"ok": True, "status": "identity", "name": name}), flush=True)


def cmd_reply(args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    sender = identity_name(home, args.sender)
    if not sender:
        die("set this session first: as <name> or receive --name <name>")
    inbound = load_last_inbound(home, sender)
    if not inbound:
        die("no inbound message to reply to; /receive first")
    target_raw = args.to or inbound.get("from")
    if not target_raw or target_raw == "anonymous":
        die("last sender was anonymous; pass --to <name>")
    text = (args.text or "").strip()
    if not text:
        die("reply text is required")
    payload = queue_message(
        home,
        sender=sender,
        target=normalize_name(str(target_raw)),
        text=text,
        reply_to=args.reply_to or inbound.get("id"),
        handoff=None,
        paths=[],
        meta={"kind": "reply"},
    )
    print(json.dumps({"ok": True, "status": "queued", "message": payload}), flush=True)


def split_handoff_source(rest: list[str], file_flag: str | None) -> tuple[str | None, str]:
    if file_flag:
        return file_flag, " ".join(rest).strip()
    if rest:
        candidate = Path(rest[0]).expanduser()
        if candidate.is_file():
            return str(candidate), " ".join(rest[1:]).strip()
    return None, " ".join(rest).strip()


def cmd_handoff(args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    sender = identity_name(home, args.sender)
    if not sender:
        die("set this session first: as <name> or receive --name <name>")
    target = normalize_name(args.to)
    file_path, text = split_handoff_source(args.text, args.file)
    file_note = load_handoff(file_path)
    note = args.note
    parts = [part for part in (note, file_note) if part]
    handoff = "\n\n".join(parts) if parts else None
    paths = []
    if file_path:
        paths.append(str(Path(file_path).expanduser()))
    if not handoff and text:
        handoff = text
        text = "handoff"
    payload = queue_message(
        home,
        sender=sender,
        target=target,
        text=text or "handoff",
        reply_to=args.reply_to,
        handoff=handoff,
        paths=paths,
        meta={"kind": "handoff"},
    )
    print(json.dumps({"ok": True, "status": "queued", "message": payload}), flush=True)


def read_next(qpath: Path, offset: int) -> tuple[dict[str, Any] | None, int]:
    if not qpath.exists():
        return None, offset
    size = qpath.stat().st_size
    if offset > size:
        offset = 0
    with qpath.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        line = handle.readline()
        new_offset = handle.tell()
    if not line:
        return None, offset
    line = line.strip()
    if not line:
        return None, new_offset
    try:
        return json.loads(line), new_offset
    except json.JSONDecodeError:
        return None, new_offset


def cmd_receive(args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    name = identity_name(home, args.name)
    if not name:
        die("pass --name or set identity with as <name>")
    register_session(home, name)
    qpath = queue_path(home, name)
    cpath = cursor_path(home, name)
    if args.live:
        # Wait only for mail appended after this receive starts.
        # Do not persist EOF yet, so unread mailbox items remain for a later drain.
        offset = qpath.stat().st_size if qpath.exists() else 0
    else:
        offset = read_offset(cpath)

    deadline = None if args.timeout == 0 else time.time() + args.timeout
    while True:
        message, new_offset = read_next(qpath, offset)
        if message is not None:
            write_offset(cpath, new_offset)
            remember_inbound(home, name, message)
            print(
                json.dumps({"ok": True, "status": "received", "message": message}),
                flush=True,
            )
            return
        if deadline is not None and time.time() >= deadline:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "status": "timeout",
                        "name": name,
                        "waited_s": args.timeout,
                    }
                ),
                flush=True,
            )
            raise SystemExit(2)
        time.sleep(0.05)


def cmd_list(_args: argparse.Namespace) -> None:
    home = bus_home()
    ensure_dirs(home)
    data = load_sessions(home)
    queues = []
    qdir = home / "queues"
    if qdir.exists():
        for path in sorted(qdir.glob("*.jsonl")):
            queues.append(
                {
                    "name": path.stem,
                    "bytes": path.stat().st_size,
                    "mtime": datetime.fromtimestamp(
                        path.stat().st_mtime, tz=timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
    print(
        json.dumps(
            {
                "ok": True,
                "home": str(home),
                "sessions": data.get("sessions", {}),
                "queues": queues,
            },
            indent=2,
        ),
        flush=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="sesstalk: local mailbox for coding sessions"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    as_cmd = sub.add_parser("as", help="Set this session's inbox name")
    as_cmd.add_argument("name")
    as_cmd.set_defaults(func=cmd_as)

    send = sub.add_parser("send", help="Queue a message for a named session")
    send.add_argument("--to", required=True)
    send.add_argument("--from", dest="sender", default="")
    send.add_argument("--reply-to", default=None, help="Optional id of the message being answered")
    send.add_argument("--note", default=None, help="Inline handoff note")
    send.add_argument("--handoff", default=None, help="Read a handoff note from a file")
    send.add_argument(
        "--path",
        action="append",
        default=None,
        help="Attach a filesystem path without embedding the file (repeatable)",
    )
    send.add_argument(
        "--meta",
        action="append",
        default=None,
        help="Extra KEY=VALUE metadata (repeatable)",
    )
    send.add_argument("text", nargs=argparse.REMAINDER)
    send.set_defaults(func=cmd_send)

    reply = sub.add_parser("reply", help="Reply to the last inbound message")
    reply.add_argument("--from", dest="sender", default="")
    reply.add_argument("--to", default="", help="Override recipient; default is last inbound from")
    reply.add_argument("--reply-to", default=None)
    reply.add_argument("text", nargs=argparse.REMAINDER)
    reply.set_defaults(func=cmd_reply)

    handoff = sub.add_parser("handoff", help="Queue a handoff note or file")
    handoff.add_argument("--to", required=True)
    handoff.add_argument("--from", dest="sender", default="")
    handoff.add_argument("--file", default=None, help="Handoff markdown/text file")
    handoff.add_argument("--note", default=None, help="Inline handoff note")
    handoff.add_argument("--reply-to", default=None)
    handoff.add_argument("text", nargs=argparse.REMAINDER)
    handoff.set_defaults(func=cmd_handoff)

    recv = sub.add_parser("receive", help="Block until a message arrives")
    recv.add_argument("--name", default="")
    recv.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Seconds to wait. 0 means wait forever.",
    )
    recv.add_argument(
        "--live",
        action="store_true",
        help="Ignore already queued mail; wait only for messages sent after this receive starts.",
    )
    recv.add_argument(
        "--drain",
        action="store_true",
        help="Deprecated. Drain/unread is now the default.",
    )
    recv.set_defaults(func=cmd_receive)

    listing = sub.add_parser("list", help="Show registered sessions and queues")
    listing.set_defaults(func=cmd_list)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd in {"send", "reply"}:
        args.text = " ".join(args.text).strip()
        if args.text.startswith("--"):
            die("put the message after options")
    args.func(args)


if __name__ == "__main__":
    main()
