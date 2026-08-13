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


WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _ws_accept_key(key: str) -> str:
    import base64
    import hashlib

    digest = hashlib.sha1((key + WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def _ws_decode_client_frame(buf: bytes) -> tuple[str | None, bytes]:
    if len(buf) < 2:
        return None, buf
    n = buf[1] & 0x7F
    masked = bool(buf[1] & 0x80)
    idx = 2
    if n == 126:
        if len(buf) < 4:
            return None, buf
        n = int.from_bytes(buf[2:4], "big")
        idx = 4
    elif n == 127:
        if len(buf) < 10:
            return None, buf
        n = int.from_bytes(buf[2:10], "big")
        idx = 10
    if masked:
        if len(buf) < idx + 4 + n:
            return None, buf
        mask = buf[idx : idx + 4]
        idx += 4
        payload = bytes(buf[idx + i] ^ mask[i % 4] for i in range(n))
        idx += n
    else:
        if len(buf) < idx + n:
            return None, buf
        payload = buf[idx : idx + n]
        idx += n
    return payload.decode("utf-8"), buf[idx:]


def _ws_encode_server_text(text: str) -> bytes:
    payload = text.encode("utf-8")
    header = bytearray([0x81])
    n = len(payload)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header.extend(n.to_bytes(2, "big"))
    else:
        header.append(127)
        header.extend(n.to_bytes(8, "big"))
    return bytes(header) + payload


def _ws_server(got: list[dict]) -> tuple[str, threading.Thread]:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def serve() -> None:
        try:
            conn, _addr = server.accept()
            with conn:
                conn.settimeout(3)
                buf = b""
                while b"\r\n\r\n" not in buf:
                    chunk = conn.recv(4096)
                    if not chunk:
                        return
                    buf += chunk
                headers, rest = buf.split(b"\r\n\r\n", 1)
                key = ""
                for line in headers.decode("iso-8859-1").split("\r\n"):
                    if line.lower().startswith("sec-websocket-key:"):
                        key = line.split(":", 1)[1].strip()
                accept = _ws_accept_key(key)
                conn.sendall(
                    (
                        "HTTP/1.1 101 Switching Protocols\r\n"
                        "Upgrade: websocket\r\n"
                        "Connection: Upgrade\r\n"
                        f"Sec-WebSocket-Accept: {accept}\r\n"
                        "\r\n"
                    ).encode("ascii")
                )
                buf = rest
                payload = None
                while payload is None:
                    payload, buf = _ws_decode_client_frame(buf)
                    if payload is not None:
                        break
                    chunk = conn.recv(4096)
                    if not chunk:
                        return
                    buf += chunk
                got.append(json.loads(payload))
                reply = json.dumps({"id": 1, "result": {"turn": {"id": "turn_ws"}}})
                conn.sendall(_ws_encode_server_text(reply))
        finally:
            server.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return f"ws://127.0.0.1:{port}/", thread


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

    def test_fake_websocket_app_server_turn_start(self) -> None:
        got: list[dict] = []
        endpoint, thread = _ws_server(got)
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_ws",
            "--app-server",
            endpoint,
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        thread.join(timeout=3)
        self.assertEqual(result.get("attention"), "started_turn", result)
        self.assertEqual(result["adapter"], "codex_app_server")
        self.assertEqual(got[0]["method"], "turn/start")
        self.assertEqual(got[0]["params"]["threadId"], "thr_ws")

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

    @unittest.skipIf(sys.platform == "win32", "unix:// Codex listen is not native Windows")
    def test_fake_unix_app_server_turn_start(self) -> None:
        sock_path = str(Path(self.temp.name) / "codex.sock")
        got: list[dict] = []
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
                    if buf.strip():
                        got.append(json.loads(buf.split(b"\n", 1)[0].decode("utf-8")))
                    conn.sendall(
                        (json.dumps({"id": 1, "result": {"turn": {"id": "turn_unix"}}}) + "\n").encode(
                            "utf-8"
                        )
                    )
            finally:
                server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(2))
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_unix",
            "--app-server",
            f"unix://{sock_path}",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        thread.join(timeout=3)
        self.assertEqual(result["attention"], "started_turn")
        self.assertEqual(got[0]["params"]["threadId"], "thr_unix")

    @unittest.skipUnless(sys.platform == "win32", "native Windows unix:// blocker")
    def test_windows_unix_app_server_is_honest_blocker(self) -> None:
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_unix",
            "--app-server",
            "unix:///tmp/codex.sock",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertIn("Windows", result["blocker"])

    @unittest.skipIf(sys.platform == "win32", "ws+unix:// is not native Windows")
    def test_fake_unix_websocket_app_server_turn_start(self) -> None:
        sock_path = str(Path(self.temp.name) / "codex-ws.sock")
        got: list[dict] = []
        ready = threading.Event()

        def serve() -> None:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server.bind(sock_path)
                server.listen(1)
                ready.set()
                conn, _addr = server.accept()
                with conn:
                    conn.settimeout(3)
                    buf = b""
                    while b"\r\n\r\n" not in buf:
                        chunk = conn.recv(4096)
                        if not chunk:
                            return
                        buf += chunk
                    headers, rest = buf.split(b"\r\n\r\n", 1)
                    key = ""
                    for line in headers.decode("iso-8859-1").split("\r\n"):
                        if line.lower().startswith("sec-websocket-key:"):
                            key = line.split(":", 1)[1].strip()
                    conn.sendall(
                        (
                            "HTTP/1.1 101 Switching Protocols\r\n"
                            "Upgrade: websocket\r\n"
                            "Connection: Upgrade\r\n"
                            f"Sec-WebSocket-Accept: {_ws_accept_key(key)}\r\n"
                            "\r\n"
                        ).encode("ascii")
                    )
                    buf = rest
                    payload = None
                    while payload is None:
                        payload, buf = _ws_decode_client_frame(buf)
                        if payload is not None:
                            break
                        chunk = conn.recv(4096)
                        if not chunk:
                            return
                        buf += chunk
                    got.append(json.loads(payload))
                    conn.sendall(
                        _ws_encode_server_text(json.dumps({"id": 1, "result": {"turn": {"id": "turn_uds_ws"}}}))
                    )
            finally:
                server.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(2))
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_uds_ws",
            "--app-server",
            f"ws+unix://{sock_path}",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        thread.join(timeout=3)
        self.assertEqual(result["attention"], "started_turn")
        self.assertEqual(got[0]["params"]["threadId"], "thr_uds_ws")

    @unittest.skipUnless(sys.platform == "win32", "native Windows ws+unix:// blocker")
    def test_windows_unix_ws_app_server_is_honest_blocker(self) -> None:
        run_cli(
            self.home,
            "bind",
            "--name",
            "codex",
            "--vendor",
            "codex",
            "--thread-id",
            "thr_uds_ws",
            "--app-server",
            "ws+unix:///tmp/codex.sock",
        )
        result = payload(run_cli(self.home, "nudge", "--name", "codex", "--vendor", "codex"))
        self.assertEqual(result["attention"], "idle_no_adapter")
        self.assertIn("Windows", result["blocker"])
