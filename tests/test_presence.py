#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli, start_receive


class PresenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_who_listening_then_idle(self) -> None:
        proc = start_receive(self.home, "b", timeout=8)
        try:
            deadline = time.time() + 3
            states = {}
            while time.time() < deadline:
                who = payload(run_cli(self.home, "who"))
                states = {peer["name"]: peer["state"] for peer in who["peers"]}
                if states.get("b") == "listening":
                    break
                time.sleep(0.1)
            self.assertEqual(states.get("b"), "listening")
            run_cli(self.home, "send", "--from", "a", "--to", "b", "hi")
            stdout, _ = proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 0, stdout)
            who2 = payload(run_cli(self.home, "who"))
            states2 = {peer["name"]: peer["state"] for peer in who2["peers"]}
            self.assertEqual(states2.get("b"), "idle")
        except Exception:
            proc.kill()
            raise

    def test_unread_count_after_send_first(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "one")
        who = payload(run_cli(self.home, "who"))
        peer = next(item for item in who["peers"] if item["name"] == "b")
        self.assertEqual(peer["unread"], 1)
        self.assertEqual(peer["state"], "idle")
        self.assertIn("last_activity", peer)

    def test_list_is_who_alias(self) -> None:
        run_cli(self.home, "send", "--from", "a", "--to", "b", "one")
        self.assertEqual(payload(run_cli(self.home, "who")), payload(run_cli(self.home, "list")))

    def test_stale_listener_expires(self) -> None:
        ldir = self.home / "listeners"
        ldir.mkdir(parents=True)
        (ldir / "ghost.json").write_text(
            json.dumps(
                {
                    "name": "ghost",
                    "pid": 999999,
                    "listening_until": time.time() + 30,
                    "updated_at": "2026-01-01T00:00:00.000Z",
                }
            ),
            encoding="utf-8",
        )
        who = payload(run_cli(self.home, "who"))
        peer = next(item for item in who["peers"] if item["name"] == "ghost")
        self.assertEqual(peer["state"], "idle")

    def test_idle_after_killed_receive(self) -> None:
        proc = start_receive(self.home, "b", timeout=30)
        deadline = time.time() + 3
        while time.time() < deadline:
            who = payload(run_cli(self.home, "who"))
            states = {peer["name"]: peer["state"] for peer in who["peers"]}
            if states.get("b") == "listening":
                break
            time.sleep(0.1)
        proc.kill()
        proc.wait(timeout=5)
        time.sleep(3.2)
        who = payload(run_cli(self.home, "who"))
        peer = next(item for item in who["peers"] if item["name"] == "b")
        self.assertEqual(peer["state"], "idle")
