#!/usr/bin/env python3
"""Mailbox tests for sesstalk. Run: python tests/test_mailbox.py"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "sesstalk.py"


def run(home: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SESSTALK_HOME"] = str(home)
    return subprocess.run(
        [sys.executable, "-S", str(CLI), *args],
        check=check,
        env=env,
        capture_output=True,
        text=True,
    )


def payload(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


class MailboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_send_first_then_receive(self) -> None:
        queued = payload(run(self.home, "send", "--from", "a", "--to", "b", "ping"))
        self.assertEqual(queued["status"], "queued")
        got = payload(run(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["status"], "received")
        self.assertEqual(got["message"]["text"], "ping")
        self.assertEqual(got["message"]["from"], "a")

    def test_reply_uses_last_inbound(self) -> None:
        run(self.home, "send", "--from", "a", "--to", "b", "ping")
        run(self.home, "receive", "--name", "b", "--timeout", "5")
        queued = payload(run(self.home, "reply", "--from", "b", "pong"))
        self.assertEqual(queued["message"]["to"], "a")
        self.assertEqual(queued["message"]["meta"]["kind"], "reply")
        got = payload(run(self.home, "receive", "--name", "a", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "pong")

    def test_live_timeout_keeps_unread(self) -> None:
        run(self.home, "send", "--from", "a", "--to", "b", "queued")
        live = run(
            self.home, "receive", "--name", "b", "--live", "--timeout", "1", check=False
        )
        self.assertEqual(live.returncode, 2)
        got = payload(run(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "queued")

    def test_handoff_note(self) -> None:
        queued = payload(
            run(self.home, "handoff", "--from", "a", "--to", "b", "--note", "next is tests")
        )
        self.assertEqual(queued["message"]["handoff"], "next is tests")
        got = payload(run(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["meta"]["kind"], "handoff")


if __name__ == "__main__":
    unittest.main()
