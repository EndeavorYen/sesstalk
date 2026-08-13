#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT


class InstallTests(unittest.TestCase):
    def test_verify_mailbox_smoke(self) -> None:
        import install

        install.verify_mailbox(ROOT / "sesstalk.py")

    def test_install_verify_isolated_home_does_not_write_agent_bus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            env["USERPROFILE"] = tmp
            home = Path(tmp)
            if os.name == "nt" and len(str(home)) >= 2 and str(home)[1] == ":":
                env["HOMEDRIVE"] = str(home)[:2]
                env["HOMEPATH"] = str(home)[2:] or "\\"
            env["SESSTALK_HOME"] = str(Path(tmp) / ".sesstalk")
            first = subprocess.run(
                [sys.executable, "-S", str(ROOT / "install.py"), "--verify", "--no-mcp", "--no-hooks"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = subprocess.run(
                [sys.executable, "-S", str(ROOT / "install.py"), "--verify", "--no-mcp", "--no-hooks"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("configured:", second.stdout)
            self.assertIn("skipped:", second.stdout)
            self.assertIn("writes_agent_bus", second.stdout)
            self.assertIn("deprecated", second.stdout.lower())
            start = second.stdout.find("{")
            self.assertGreaterEqual(start, 0)
            blob = second.stdout[start:]
            depth = 0
            cut = None
            for i, ch in enumerate(blob):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        cut = blob[: i + 1]
                        break
            payload = json.loads(cut)
            self.assertFalse(payload["writes_agent_bus"])
            self.assertFalse((Path(tmp) / ".agent-bus").exists())
            self.assertTrue((Path(tmp) / ".sesstalk" / "sesstalk.py").is_file())
