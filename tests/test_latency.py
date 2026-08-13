#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import CLI, run_cli

WARMUP = 2
SAMPLES = 12
CLI_P95_BUDGET_MS = 2000
MCP_P95_BUDGET_MS = 300


def _frame(message: dict) -> bytes:
    raw = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw


def _read_rpc(stdout) -> dict:
    header_lines = []
    while True:
        line = stdout.readline()
        if not line:
            raise AssertionError("MCP stdout closed")
        if line in (b"\r\n", b"\n"):
            break
        header_lines.append(line)
    length = 0
    for raw in header_lines:
        decoded = raw.decode("ascii", errors="replace")
        if decoded.lower().startswith("content-length:"):
            length = int(decoded.split(":", 1)[1].strip())
    body = stdout.read(length)
    return json.loads(body.decode("utf-8"))


class LatencyTests(unittest.TestCase):
    def test_cli_send_p95_under_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for i in range(WARMUP):
                run_cli(home, "send", "--from", "a", "--to", "b", f"warmup-{i}")
            samples_ms = []
            for i in range(SAMPLES):
                start = perf_counter()
                run_cli(home, "send", "--from", "a", "--to", "b", f"sample-{i}")
                samples_ms.append((perf_counter() - start) * 1000)
            samples_ms.sort()
            idx = max(0, int(round(0.95 * (len(samples_ms) - 1))))
            p95 = samples_ms[idx]
            mean = statistics.mean(samples_ms)
            print(f"cli_send_ms mean={mean:.1f} p95={p95:.1f} budget={CLI_P95_BUDGET_MS}")
            self.assertLess(p95, CLI_P95_BUDGET_MS, f"p95 {p95:.1f}ms >= {CLI_P95_BUDGET_MS}ms")

    def test_inprocess_send_p95_under_300ms(self) -> None:
        import sesstalk as st

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SESSTALK_HOME"] = tmp
            home = st.bus_home()
            st.ensure_dirs(home)
            for i in range(WARMUP):
                st.queue_message(
                    home,
                    sender="a",
                    target="b",
                    text=f"warmup-{i}",
                    reply_to=None,
                    handoff=None,
                    paths=[],
                    meta={},
                )
            samples_ms = []
            for i in range(SAMPLES):
                start = perf_counter()
                st.queue_message(
                    home,
                    sender="a",
                    target="b",
                    text=f"sample-{i}",
                    reply_to=None,
                    handoff=None,
                    paths=[],
                    meta={},
                )
                samples_ms.append((perf_counter() - start) * 1000)
            samples_ms.sort()
            idx = max(0, int(round(0.95 * (len(samples_ms) - 1))))
            p95 = samples_ms[idx]
            print(f"inprocess_send_ms p95={p95:.1f} budget={MCP_P95_BUDGET_MS}")
            self.assertLess(p95, MCP_P95_BUDGET_MS, f"p95 {p95:.1f}ms >= {MCP_P95_BUDGET_MS}ms")

    def test_mcp_send_p95_under_300ms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["SESSTALK_HOME"] = tmp
            proc = subprocess.Popen(
                [sys.executable, "-u", "-S", str(CLI), "mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=0,
            )
            assert proc.stdin and proc.stdout
            try:
                proc.stdin.write(_frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
                proc.stdin.flush()
                _read_rpc(proc.stdout)

                def call_send(i: int) -> None:
                    msg = {
                        "jsonrpc": "2.0",
                        "id": 10 + i,
                        "method": "tools/call",
                        "params": {
                            "name": "sesstalk_send",
                            "arguments": {"to": "b", "sender": "a", "text": f"m-{i}"},
                        },
                    }
                    proc.stdin.write(_frame(msg))
                    proc.stdin.flush()
                    reply = _read_rpc(proc.stdout)
                    if "result" not in reply:
                        raise AssertionError(reply)

                for i in range(WARMUP):
                    call_send(i)
                samples_ms = []
                for i in range(SAMPLES):
                    start = perf_counter()
                    call_send(100 + i)
                    samples_ms.append((perf_counter() - start) * 1000)
                samples_ms.sort()
                idx = max(0, int(round(0.95 * (len(samples_ms) - 1))))
                p95 = samples_ms[idx]
                print(f"mcp_send_ms p95={p95:.1f} budget={MCP_P95_BUDGET_MS}")
                self.assertLess(p95, MCP_P95_BUDGET_MS, f"p95 {p95:.1f}ms >= {MCP_P95_BUDGET_MS}ms")
            finally:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                except OSError:
                    pass
                proc.kill()
                proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
