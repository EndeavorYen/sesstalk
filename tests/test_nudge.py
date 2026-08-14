#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli, start_receive


class NudgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_idle_no_adapter_for_each_vendor(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "peer", "queued")
        for vendor in ("cursor", "claude", "codex", "grok", "hermes"):
            result = payload(
                run_cli(self.home, "nudge", "--name", "peer", "--vendor", vendor)
            )
            self.assertEqual(result["attention"], "idle_no_adapter", vendor)
            self.assertEqual(result["status"], "queued")

    def test_nudge_accepts_positional_peer(self) -> None:
        result = payload(run_cli(self.home, "nudge", "hermes", "--vendor", "grok"))
        self.assertEqual(result["name"], "hermes")
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertIn("receive", result["blocker"])

    def test_grok_bind_does_not_claim_hook_armed(self) -> None:
        run_cli(self.home, "init", "--name", "hermes", "--vendor", "grok")
        result = payload(run_cli(self.home, "nudge", "--name", "hermes", "--vendor", "grok"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertNotEqual(result["attention"], "hook_armed")
        self.assertIn("receive", result["blocker"])

    def test_fake_adapter_started_turn(self) -> None:
        result = payload(
            run_cli(
                self.home,
                "nudge",
                "--name",
                "peer",
                "--vendor",
                "cursor",
                extra_env={"SESSTALK_NUDGE_ADAPTER": "fake_started"},
            )
        )
        self.assertEqual(result["attention"], "started_turn")

    def test_fake_adapter_fail(self) -> None:
        result = run_cli(
            self.home,
            "nudge",
            "--name",
            "peer",
            "--vendor",
            "claude",
            extra_env={"SESSTALK_NUDGE_ADAPTER": "fake_fail"},
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        body = payload(result)
        self.assertEqual(body["attention"], "error")

    def test_nudge_reports_listening(self) -> None:
        proc = start_receive(self.home, "peer", timeout=8)
        try:
            deadline = time.time() + 3
            attention = None
            while time.time() < deadline:
                result = payload(run_cli(self.home, "nudge", "--name", "peer", "--vendor", "cursor"))
                attention = result["attention"]
                if attention == "listening":
                    break
                time.sleep(0.1)
            self.assertEqual(attention, "listening")
        finally:
            proc.kill()
            proc.wait(timeout=5)
