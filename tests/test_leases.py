#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class LeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_claim_then_conflict(self) -> None:
        claimed = payload(
            run_cli(
                self.home,
                "claim",
                "--from",
                "a",
                "--path",
                "src/auth.ts",
                "--ttl",
                "300",
                "--thread",
                "auth-review",
            )
        )
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["lease"]["owner"], "a")
        refused = run_cli(
            self.home, "claim", "--from", "b", "--path", "src/auth.ts", check=False
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("a", payload(refused)["error"])

    def test_owner_can_release(self) -> None:
        run_cli(self.home, "claim", "--from", "a", "--path", "src/auth.ts")
        payload(run_cli(self.home, "release", "--from", "a", "--path", "src/auth.ts"))
        listed = payload(run_cli(self.home, "claims"))
        self.assertEqual(listed["leases"], [])

    def test_expired_lease_is_free(self) -> None:
        run_cli(self.home, "claim", "--from", "a", "--path", "src/auth.ts", "--ttl", "0")
        claimed = payload(run_cli(self.home, "claim", "--from", "b", "--path", "src/auth.ts"))
        self.assertEqual(claimed["lease"]["owner"], "b")

    def test_who_lists_leases(self) -> None:
        run_cli(self.home, "claim", "--from", "a", "--path", "src/auth.ts")
        who = payload(run_cli(self.home, "who"))
        self.assertTrue(any(item["path"].endswith("auth.ts") for item in who["leases"]))
