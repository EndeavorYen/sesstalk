#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_cursor_stop_followup_when_unread(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "peer", "please review")
        event = {"hook_event_name": "stop", "status": "completed", "loop_count": 0}
        result = run_cli(
            self.home,
            "hook",
            "--vendor",
            "cursor",
            "--name",
            "peer",
            stdin=json.dumps(event),
        )
        body = json.loads(result.stdout)
        self.assertIn("followup_message", body)
        self.assertIn("please review", body["followup_message"])

    def test_cursor_stop_silent_when_empty(self) -> None:
        event = {"hook_event_name": "stop", "status": "completed", "loop_count": 0}
        result = run_cli(self.home, "hook", "--vendor", "cursor", "--name", "peer", stdin=json.dumps(event))
        self.assertEqual(json.loads(result.stdout), {})

    def test_claude_stop_blocks_when_unread(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "peer", "hello")
        event = {"hook_event_name": "Stop", "stop_hook_active": False}
        result = run_cli(
            self.home, "hook", "--vendor", "claude", "--name", "peer", stdin=json.dumps(event)
        )
        body = json.loads(result.stdout)
        self.assertEqual(body["decision"], "block")
        self.assertIn("hello", body["reason"])

    def test_claude_does_not_loop(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "peer", "hello")
        event = {"hook_event_name": "Stop", "stop_hook_active": True}
        result = run_cli(
            self.home, "hook", "--vendor", "claude", "--name", "peer", stdin=json.dumps(event)
        )
        self.assertEqual(json.loads(result.stdout), {})

    def test_bind_makes_nudge_hook_armed(self) -> None:
        run_cli(self.home, "bind", "--name", "peer", "--vendor", "cursor")
        result = payload(run_cli(self.home, "nudge", "--name", "peer", "--vendor", "cursor"))
        self.assertEqual(result["attention"], "hook_armed")
        self.assertEqual(result["status"], "queued")

    def test_hook_maps_cwd_to_bound_inbox(self) -> None:
        ws_a = self.home / "proj-a"
        ws_b = self.home / "proj-b"
        ws_a.mkdir()
        ws_b.mkdir()
        run_cli(self.home, "bind", "--name", "cursor-a", "--vendor", "cursor", cwd=ws_a)
        run_cli(self.home, "bind", "--name", "cursor-b", "--vendor", "cursor", cwd=ws_b)
        run_cli(self.home, "send", "--from", "claude", "--to", "cursor-a", "review a")
        event = json.dumps({"hook_event_name": "stop", "status": "completed", "loop_count": 0})
        hit = run_cli(self.home, "hook", "--vendor", "cursor", stdin=event, cwd=ws_a)
        body = json.loads(hit.stdout)
        self.assertIn("followup_message", body)
        self.assertIn("review a", body["followup_message"])
        miss = run_cli(self.home, "hook", "--vendor", "cursor", stdin=event, cwd=ws_b)
        self.assertEqual(json.loads(miss.stdout), {})

    def test_hook_stays_silent_when_two_binds_share_cwd(self) -> None:
        ws = self.home / "shared"
        ws.mkdir()
        run_cli(self.home, "bind", "--name", "cursor-a", "--vendor", "cursor", cwd=ws)
        run_cli(self.home, "bind", "--name", "cursor-b", "--vendor", "cursor", cwd=ws)
        run_cli(self.home, "send", "--from", "claude", "--to", "cursor-a", "do not wake the wrong chat")
        event = json.dumps({"hook_event_name": "stop", "status": "completed", "loop_count": 0})
        result = run_cli(self.home, "hook", "--vendor", "cursor", stdin=event, cwd=ws)
        self.assertEqual(json.loads(result.stdout), {})
