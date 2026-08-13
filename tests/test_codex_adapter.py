#!/usr/bin/env python3
from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import payload, run_cli


def _jsonl_server(got: list[dict]) -> tuple[str, threading.Thread, callable]:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def serve() -> None:
        try:
            conn, _addr = server.accept()
            with conn:
                conn.settimeout(2)
                buf = b""
                while b"\n" not in buf:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                if buf.strip():
                    got.append(json.loads(buf.split(b"\n", 1)[0].decode("utf-8")))
                reply = json.dumps({"id": 1, "result": {"turn": {"id": "turn_fake"}}}) + "\n"
                conn.sendall(reply.encode("utf-8"))
        finally:
            server.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return f"tcp://127.0.0.1:{port}", thread, lambda: server.close()


class CodexAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_thread_id_without_app_server_is_idle(self) -> None:
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_live",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertIn("spawn", result["blocker"].lower())
        self.assertNotEqual(result.get("status"), "started_turn")

    def test_fake_app_server_turn_start(self) -> None:
        got: list[dict] = []
        endpoint, thread, _close = _jsonl_server(got)
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_live",
            "--app-server",
            endpoint,
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        thread.join(timeout=3)
        self.assertEqual(result["attention"], "started_turn")
        self.assertEqual(result["adapter"], "codex_app_server")
        self.assertEqual(got[0]["method"], "turn/start")
        self.assertEqual(got[0]["params"]["threadId"], "thr_live")

    def test_nudge_does_not_spawn_codex_process(self) -> None:
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_live",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        source = Path(__file__).resolve().parents[1] / "sesstalk.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("Popen(", text)
        self.assertNotIn('["codex"', text)
        self.assertNotIn("['codex'", text)
