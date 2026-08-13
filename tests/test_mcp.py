#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import CLI, payload, run_cli


def mcp_exchange(messages: list[dict], home: Path | None = None) -> list[dict]:
    env = os.environ.copy()
    if home is not None:
        env["SESSTALK_HOME"] = str(home)
    proc = subprocess.Popen(
        [sys.executable, "-S", str(CLI), "mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    blobs = []
    for message in messages:
        raw = json.dumps(message).encode("utf-8")
        blobs.append(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
    stdout, _stderr = proc.communicate(b"".join(blobs), timeout=10)
    replies = []
    buf = stdout
    while buf:
        sep = buf.find(b"\r\n\r\n")
        if sep < 0:
            break
        header = buf[:sep].decode("ascii", errors="replace")
        length = 0
        for line in header.split("\r\n"):
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
        start = sep + 4
        body = buf[start : start + length]
        replies.append(json.loads(body.decode("utf-8")))
        buf = buf[start + length :]
    return replies


class McpTests(unittest.TestCase):
    def test_initialize_and_list_tools(self) -> None:
        replies = mcp_exchange(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            ]
        )
        self.assertGreaterEqual(len(replies), 2)
        self.assertEqual(replies[0]["result"]["serverInfo"]["name"], "sesstalk")
        names = [tool["name"] for tool in replies[1]["result"]["tools"]]
        self.assertIn("sesstalk_send", names)
        self.assertIn("sesstalk_nudge", names)
        self.assertIn("sesstalk_peek", names)
        self.assertIn("sesstalk_doctor", names)
        self.assertIn("sesstalk_log", names)
        self.assertIn("sesstalk_init", names)
        self.assertIn("sesstalk_schema", names)
        self.assertEqual(replies[0]["result"]["serverInfo"]["version"], "0.5.1")

    def test_send_tool_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            replies = mcp_exchange(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "sesstalk_send",
                            "arguments": {"to": "b", "sender": "a", "text": "via-mcp"},
                        },
                    }
                ],
                home=home,
            )
            self.assertEqual(len(replies), 1)
            inner = json.loads(replies[0]["result"]["content"][0]["text"])
            self.assertEqual(inner["status"], "queued")
            got = payload(run_cli(home, "receive", "--name", "b", "--timeout", "5"))
            self.assertEqual(got["message"]["text"], "via-mcp")
            self.assertTrue(got["message"]["provenance"]["untrusted"])

    def test_send_fanout_via_comma_to(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            replies = mcp_exchange(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {
                            "name": "sesstalk_send",
                            "arguments": {
                                "to": "b,c",
                                "sender": "a",
                                "text": "fan",
                                "thread": "t9",
                            },
                        },
                    }
                ],
                home=home,
            )
            inner = json.loads(replies[0]["result"]["content"][0]["text"])
            self.assertEqual(len(inner["messages"]), 2)
            peeked = payload(run_cli(home, "peek", "--name", "c"))
            self.assertEqual(peeked["next"]["thread"], "t9")

    def test_init_tool_binds_vendor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            replies = mcp_exchange(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": "tools/call",
                        "params": {
                            "name": "sesstalk_init",
                            "arguments": {"name": "peer", "vendor": "cursor"},
                        },
                    }
                ],
                home=home,
            )
            inner = json.loads(replies[0]["result"]["content"][0]["text"])
            self.assertEqual(inner["status"], "ready")
            self.assertEqual(inner["bind"]["vendor"], "cursor")

