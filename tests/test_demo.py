#!/usr/bin/env python3
"""sesstalk demo must reproduce the README story without an LLM."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class DemoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_demo_json_reproduces_readme_story(self) -> None:
        proc = run_cli(self.home, "demo", "--json")
        data = payload(proc)
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "demo")
        self.assertEqual(data["thread"], "auth-review")
        self.assertEqual({msg["to"] for msg in data["fanout"]}, {"claude", "codex"})
        for msg in data["fanout"]:
            self.assertEqual(msg["audience"], ["claude", "codex"])
            self.assertEqual(msg["thread"], "auth-review")
            self.assertEqual(msg["goal"], "Ship refresh-token rotation")
            self.assertEqual(msg["from"], "cursor-a")
        self.assertEqual(data["received"]["to"], "claude")
        self.assertEqual(data["received"]["thread"], "auth-review")
        self.assertEqual(data["reply"]["to"], "cursor-a")
        self.assertEqual(data["reply"]["thread"], "auth-review")
        self.assertEqual(data["reply"]["text"], "looks good, next is tests")
        self.assertEqual(data["reply"]["provenance"]["depth"], 1)
        self.assertTrue(data["reply"]["provenance"]["untrusted"])

    def test_demo_does_not_write_caller_mailbox(self) -> None:
        run_cli(self.home, "demo", "--json")
        queues = self.home / "queues"
        self.assertFalse(queues.exists())

    def test_demo_human_output_shows_commands(self) -> None:
        proc = run_cli(self.home, "demo")
        self.assertIn("auth-review", proc.stdout)
        self.assertIn("sesstalk send", proc.stdout)
        self.assertIn("sesstalk reply", proc.stdout)
