#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class OpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_version_reports_semver(self) -> None:
        data = payload(run_cli(self.home, "version"))
        self.assertTrue(data["ok"])
        self.assertRegex(data["version"], r"^\d+\.\d+\.\d+$")

    def test_init_sets_identity_and_hook_armed(self) -> None:
        ready = payload(run_cli(self.home, "init", "--name", "peer", "--vendor", "cursor"))
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["name"], "peer")
        self.assertEqual(ready["bind"]["vendor"], "cursor")
        nudge = payload(run_cli(self.home, "nudge", "--name", "peer", "--vendor", "cursor"))
        self.assertEqual(nudge["attention"], "hook_armed")

    def test_log_does_not_consume(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "keep-me")
        logged = payload(run_cli(self.home, "log", "--name", "b"))
        self.assertEqual(logged["status"], "log")
        self.assertEqual(logged["count"], 1)
        self.assertEqual(logged["messages"][0]["text"], "keep-me")
        got = payload(run_cli(self.home, "receive", "--name", "b", "--timeout", "5"))
        self.assertEqual(got["message"]["text"], "keep-me")

    def test_doctor_sees_home_and_identity(self) -> None:
        run_cli(self.home, "as", "cursor-a")
        data = payload(run_cli(self.home, "doctor"))
        self.assertTrue(data["ok"])
        self.assertEqual(Path(data["home"]), self.home)
        self.assertEqual(data["identities"], ["cursor-a"])
        self.assertIn("version", data)
        run_cli(self.home, "send", "--from", "cursor-a", "--to", "claude", "--thread", "auth-review", "ping")
        data = payload(run_cli(self.home, "doctor"))
        self.assertEqual(data["mailboxes"]["claude"]["unread"], 1)
        self.assertEqual(data["mailboxes"]["claude"]["last_thread"], "auth-review")
        self.assertEqual(data["mailboxes"]["claude"]["corrupt"], 0)

    def test_schema_lists_contract_keys(self) -> None:
        data = payload(run_cli(self.home, "schema"))
        self.assertEqual(data["status"], "schema")
        self.assertEqual(data["schema"]["type"], "object")
        self.assertIn("goal", data["schema"]["required"])
        self.assertIn("provenance", data["schema"]["required"])
