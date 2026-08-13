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


class ClaudeSocketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @unittest.skipIf(sys.platform == "win32", "Claude inbox sockets are Unix-domain, not native Windows")
    def test_fake_uds_nudge_started_turn(self) -> None:
        sock_path = str(Path(self.temp.name) / "claude.sock")
        received: list[bytes] = []
        ready = threading.Event()

        def serve() -> None:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server.bind(sock_path)
                server.listen(1)
                ready.set()
                conn, _addr = server.accept()
                with conn:
                    conn.settimeout(2)
                    buf = b""
                    while b"\n" not in buf:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                    received.append(buf)
            finally:
                server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(2))
        run_cli(
            self.home,
            "bind",
            "--name",
            "claude",
            "--vendor",
            "claude",
            "--socket",
            sock_path,
        )
        result = payload(run_cli(self.home, "nudge", "--name", "claude", "--vendor", "claude"))
        thread.join(timeout=3)
        self.assertEqual(result["attention"], "started_turn")
        self.assertEqual(result["adapter"], "claude_socket")
        self.assertTrue(received)
        body = json.loads(received[0].split(b"\n", 1)[0].decode("utf-8"))
        self.assertEqual(body["type"], "message")

    @unittest.skipUnless(sys.platform == "win32", "native Windows blocker")
    def test_windows_unix_socket_path_is_honest_blocker(self) -> None:
        run_cli(
            self.home,
            "bind",
            "--name",
            "claude",
            "--vendor",
            "claude",
            "--socket",
            "/tmp/claude.sock",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "claude", "--vendor", "claude"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertIn("Windows", result["blocker"])
        self.assertNotEqual(result.get("status"), "started_turn")
