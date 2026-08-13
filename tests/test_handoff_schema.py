#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class HandoffSchemaTests(unittest.TestCase):
    def test_goal_next_questions_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.md"
            note.write_text("details", encoding="utf-8")
            home = Path(tmp) / "home"
            queued = payload(
                run_cli(
                    home,
                    "handoff",
                    "--from",
                    "a",
                    "--to",
                    "b",
                    "--goal",
                    "ship auth",
                    "--done",
                    "tests green",
                    "--next",
                    "rotate tokens",
                    "--question",
                    "bcrypt 5?",
                    "--file",
                    str(note),
                )
            )
            msg = queued["message"]
            self.assertEqual(msg["goal"], "ship auth")
            self.assertEqual(msg["done"], "tests green")
            self.assertEqual(msg["next"], "rotate tokens")
            self.assertEqual(msg["questions"], ["bcrypt 5?"])
            self.assertEqual(msg["files"], msg["paths"])
            self.assertTrue(msg["files"][0].endswith("note.md"))
            self.assertEqual(msg["meta"]["kind"], "handoff")
            self.assertTrue(msg["provenance"]["untrusted"])

    def test_handoff_without_goal_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            refused = run_cli(
                home,
                "handoff",
                "--from",
                "a",
                "--to",
                "b",
                "--note",
                "next is tests",
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("goal", payload(refused)["error"])
