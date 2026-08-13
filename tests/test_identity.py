#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class IdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_as_in_two_directories_does_not_clobber_send(self) -> None:
        ws_a = self.home / "ws-a"
        ws_b = self.home / "ws-b"
        ws_a.mkdir()
        ws_b.mkdir()
        run_cli(self.home, "as", "cursor-a", cwd=ws_a)
        run_cli(self.home, "as", "cursor-b", cwd=ws_b)
        from_a = payload(run_cli(self.home, "send", "--to", "peer", "from-a", cwd=ws_a))
        from_b = payload(run_cli(self.home, "send", "--to", "peer", "from-b", cwd=ws_b))
        self.assertEqual(from_a["message"]["from"], "cursor-a")
        self.assertEqual(from_b["message"]["from"], "cursor-b")

    def test_two_as_same_cwd_requires_explicit_from(self) -> None:
        ws = self.home / "shared"
        ws.mkdir()
        run_cli(self.home, "as", "cursor-a", cwd=ws)
        second = payload(run_cli(self.home, "as", "cursor-b", cwd=ws))
        self.assertIn("warning", second)
        failed = run_cli(self.home, "send", "--to", "peer", "nope", cwd=ws, check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("--from", payload(failed)["error"])
        explicit = payload(
            run_cli(self.home, "send", "--from", "cursor-a", "--to", "peer", "ok", cwd=ws)
        )
        self.assertEqual(explicit["message"]["from"], "cursor-a")

    def test_env_name_wins_over_cwd_identity(self) -> None:
        ws = self.home / "ws"
        ws.mkdir()
        run_cli(self.home, "as", "cursor-a", cwd=ws)
        queued = payload(
            run_cli(
                self.home,
                "send",
                "--to",
                "peer",
                "via-env",
                cwd=ws,
                extra_env={"SESSTALK_NAME": "cursor-b"},
            )
        )
        self.assertEqual(queued["message"]["from"], "cursor-b")

    def test_who_warns_when_cwd_has_two_as_names(self) -> None:
        ws = self.home / "shared"
        ws.mkdir()
        run_cli(self.home, "as", "cursor-a", cwd=ws)
        run_cli(self.home, "as", "cursor-b", cwd=ws)
        who = payload(run_cli(self.home, "who", cwd=ws))
        self.assertEqual(sorted(who["identities"]), ["cursor-a", "cursor-b"])
        self.assertIn("warning", who)

    def test_who_has_no_warning_for_single_as(self) -> None:
        ws = self.home / "solo"
        ws.mkdir()
        run_cli(self.home, "as", "cursor-a", cwd=ws)
        who = payload(run_cli(self.home, "who", cwd=ws))
        self.assertEqual(who["identities"], ["cursor-a"])
        self.assertNotIn("warning", who)
