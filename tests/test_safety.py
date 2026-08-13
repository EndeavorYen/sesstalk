#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class SafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_send_has_untrusted_provenance_depth_zero(self) -> None:
        queued = payload(run_cli(self.home, "send", "--from", "a", "--to", "b", "ping"))
        prov = queued["message"]["provenance"]
        self.assertTrue(prov["untrusted"])
        self.assertEqual(prov["peer"], "a")
        self.assertEqual(prov["depth"], 0)

    def test_reply_increments_depth_and_third_hop_is_refused(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "one")
        run_cli(self.home, "receive", "--name", "b", "--timeout", "5")
        hop1 = payload(run_cli(self.home, "reply", "--from", "b", "two"))
        self.assertEqual(hop1["message"]["provenance"]["depth"], 1)
        run_cli(self.home, "receive", "--name", "a", "--timeout", "5")
        refused = run_cli(self.home, "reply", "--from", "a", "three", check=False)
        self.assertNotEqual(refused.returncode, 0)
        err = payload(refused)
        self.assertIn("depth", err["error"])

    def test_explicit_depth_zero_and_one_ok(self) -> None:
        zero = payload(run_cli(self.home, "send", "--from", "a", "--to", "b", "--depth", "0", "ok"))
        self.assertEqual(zero["message"]["provenance"]["depth"], 0)
        one = payload(run_cli(self.home, "send", "--from", "a", "--to", "c", "--depth", "1", "ok"))
        self.assertEqual(one["message"]["provenance"]["depth"], 1)

    def test_explicit_depth_two_is_refused(self) -> None:
        refused = run_cli(
            self.home, "send", "--from", "a", "--to", "b", "--depth", "2", "nope", check=False
        )
        self.assertNotEqual(refused.returncode, 0)
