#!/usr/bin/env python3
"""Golden envelope contract. Expand fields here when the schema changes."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "envelope.example.json"
REQUIRED = (
    "id",
    "ts",
    "from",
    "to",
    "reply_to",
    "text",
    "handoff",
    "goal",
    "done",
    "next",
    "questions",
    "paths",
    "files",
    "meta",
    "provenance",
)


class ContractTests(unittest.TestCase):
    def test_example_envelope_has_required_keys(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for key in REQUIRED:
            self.assertIn(key, data)
        self.assertIsInstance(data["paths"], list)
        self.assertIsInstance(data["files"], list)
        self.assertIsInstance(data["questions"], list)
        self.assertTrue(data["provenance"]["untrusted"])

    def test_cli_send_emits_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            msg = payload(run_cli(Path(tmp), "send", "--from", "a", "--to", "b", "ping"))["message"]
            for key in REQUIRED:
                self.assertIn(key, msg)
            self.assertEqual(msg["files"], msg["paths"])
            self.assertTrue(msg["provenance"]["untrusted"])
            self.assertEqual(msg["provenance"]["depth"], 0)


if __name__ == "__main__":
    unittest.main()
