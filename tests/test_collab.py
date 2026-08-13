#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class CollabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_fanout_same_thread_two_inboxes(self) -> None:
        queued = payload(
            run_cli(
                self.home,
                "send",
                "--from",
                "a",
                "--to",
                "b",
                "--to",
                "c",
                "--thread",
                "auth-review",
                "please review",
            )
        )
        self.assertEqual(len(queued["messages"]), 2)
        self.assertEqual(queued["thread"], "auth-review")
        self.assertEqual(queued["messages"][0]["audience"], ["b", "c"])
        got_b = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        got_c = payload(run_cli(self.home, "receive", "--name", "c", "--timeout", "5"))
        self.assertEqual(got_b["message"]["thread"], "auth-review")
        self.assertEqual(got_c["message"]["thread"], "auth-review")
        self.assertEqual(got_b["message"]["to"], "b")
        self.assertEqual(got_c["message"]["to"], "c")
        self.assertNotEqual(got_b["message"]["id"], got_c["message"]["id"])

    def test_comma_to_is_fanout(self) -> None:
        queued = payload(run_cli(self.home, "send", "--from", "a", "--to", "b,c", "hi"))
        self.assertEqual([m["to"] for m in queued["messages"]], ["b", "c"])

    def test_reply_inherits_thread(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "--thread", "t1", "ping")
        run_cli(self.home, "receive", "--name", "b", "--timeout", "5")
        queued = payload(run_cli(self.home, "reply", "--from", "b", "pong"))
        self.assertEqual(queued["message"]["thread"], "t1")
        self.assertEqual(queued["message"]["to"], "a")

    def test_peek_does_not_consume(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "secret")
        peeked = payload(run_cli(self.home, "peek", "--name", "b"))
        self.assertEqual(peeked["unread"], 1)
        self.assertEqual(peeked["next"]["text"], "secret")
        peeked2 = payload(run_cli(self.home, "peek", "--name", "b"))
        self.assertEqual(peeked2["unread"], 1)
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "secret")

    def test_drain_consumes_all_without_blocking(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "one")
        run_cli(self.home, "send", "--from", "a", "--to", "b", "two")
        drained = payload(run_cli(self.home, "receive", "--name", "b", "--drain"))
        self.assertEqual(drained["status"], "drained")
        self.assertEqual(drained["count"], 2)
        self.assertEqual([m["text"] for m in drained["messages"]], ["one", "two"])
        empty = payload(run_cli(self.home, "receive", "--name", "b", "--drain"))
        self.assertEqual(empty["count"], 0)
        peeked = payload(run_cli(self.home, "peek", "--name", "b"))
        self.assertIsNone(peeked["next"])
