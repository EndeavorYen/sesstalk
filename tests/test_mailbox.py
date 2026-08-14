#!/usr/bin/env python3
"""Fake-peer mailbox tests. No LLM. Run: python -m unittest discover -s tests"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli, start_receive


class MailboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_send_first_then_receive(self) -> None:
        queued = payload(run_cli(self.home, "send", "--from", "a", "--to", "b", "ping"))
        self.assertEqual(queued["status"], "queued")
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["status"], "received")
        self.assertEqual(got["message"]["text"], "ping")
        self.assertEqual(got["message"]["from"], "a")

    def test_receive_first_then_send(self) -> None:
        proc = start_receive(self.home, "b", timeout=8)
        time.sleep(0.4)
        run_cli(self.home, "send", "--from", "a", "--to", "b", "hello-live")
        stdout, _stderr = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 0, stdout)
        got = json.loads(stdout)
        self.assertEqual(got["message"]["text"], "hello-live")

    def test_reply_uses_last_inbound(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "ping")
        run_cli(self.home, "receive", "--name", "b", "--timeout", "5")
        queued = payload(run_cli(self.home, "reply", "--from", "b", "pong"))
        self.assertEqual(queued["message"]["to"], "a")
        self.assertEqual(queued["message"]["meta"]["kind"], "reply")
        got = payload(run_cli(self.home, "receive", "--name", "a", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "pong")

    def test_live_timeout_keeps_unread(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "queued")
        live = run_cli(
            self.home, "receive", "--name", "b", "--live", "--timeout", "1", check=False
        )
        self.assertEqual(live.returncode, 2)
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "queued")

    def test_handoff_note(self) -> None:
        queued = payload(
            run_cli(
                self.home,
                "handoff",
                "--from",
                "a",
                "--to",
                "b",
                "--goal",
                "finish tests",
                "--note",
                "next is tests",
            )
        )
        self.assertEqual(queued["message"]["handoff"], "next is tests")
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["meta"]["kind"], "handoff")

    def test_two_inboxes_do_not_clobber_reply_target(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "for-b")
        run_cli(self.home, "send", "--from", "c", "--to", "d", "for-d")
        run_cli(self.home, "receive", "--name", "b", "--timeout", "5")
        run_cli(self.home, "receive", "--name", "d", "--timeout", "5")
        reply_b = payload(run_cli(self.home, "reply", "--from", "b", "ack-b"))
        reply_d = payload(run_cli(self.home, "reply", "--from", "d", "ack-d"))
        self.assertEqual(reply_b["message"]["to"], "a")
        self.assertEqual(reply_d["message"]["to"], "c")

    def test_concurrent_sends_are_readable_in_order(self) -> None:
        def send(text: str) -> None:
            run_cli(self.home, "send", "--from", "a", "--to", "inbox", text)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(send, f"m{i}") for i in range(2)]
            for fut in futs:
                fut.result()
        first = payload(run_cli(self.home, "receive", "--name", "inbox", "--timeout", "5"))
        second = payload(run_cli(self.home, "receive", "--name", "inbox", "--timeout", "5"))
        texts = {first["message"]["text"], second["message"]["text"]}
        self.assertEqual(texts, {"m0", "m1"})

    def test_many_concurrent_sends_keep_unique_ids(self) -> None:
        def send(text: str) -> str:
            return payload(run_cli(self.home, "send", "--from", "a", "--to", "inbox", text))["message"]["id"]

        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = [pool.submit(send, f"m{i}") for i in range(24)]
            ids = [fut.result() for fut in futs]
        self.assertEqual(len(ids), len(set(ids)))
        drained = payload(run_cli(self.home, "receive", "--name", "inbox", "--drain", "--timeout", "5"))
        self.assertEqual(drained["count"], 24)

    def test_pid_alive_does_not_terminate_self(self) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import sesstalk

        pid = os.getpid()
        self.assertTrue(sesstalk.pid_alive(pid))
        self.assertTrue(sesstalk.pid_alive(pid))
        self.assertEqual(os.getpid(), pid)
        self.assertFalse(sesstalk.pid_alive(999999))

    def test_stale_lock_from_dead_pid_is_cleared(self) -> None:
        qdir = self.home / "queues"
        qdir.mkdir(parents=True)
        (qdir / "b.lock").write_text("999999", encoding="utf-8")
        queued = payload(run_cli(self.home, "send", "--from", "a", "--to", "b", "after-stale-lock"))
        self.assertEqual(queued["status"], "queued")

    def test_corrupt_line_does_not_block_next_message(self) -> None:
        qdir = self.home / "queues"
        qdir.mkdir(parents=True)
        (qdir / "b.jsonl").write_text("not-json\n", encoding="utf-8")
        run_cli(self.home, "send", "--from", "a", "--to", "b", "after-junk")
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "after-junk")


if __name__ == "__main__":
    unittest.main()
