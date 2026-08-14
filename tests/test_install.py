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


def _isolated_env(tmp: str) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = tmp
    env["USERPROFILE"] = tmp
    home = Path(tmp)
    if os.name == "nt" and len(str(home)) >= 2 and str(home)[1] == ":":
        env["HOMEDRIVE"] = str(home)[:2]
        env["HOMEPATH"] = str(home)[2:] or "\\"
    env["SESSTALK_HOME"] = str(home / ".sesstalk")
    keep = [str(Path(sys.executable).parent), "/usr/bin", "/bin", "/usr/local/bin"]
    if os.name == "nt":
        keep = [p for p in env.get("PATH", "").split(os.pathsep) if p and "sesstalk" not in p.lower()]
    env["PATH"] = os.pathsep.join(keep)
    return env


def _first_json(stdout: str) -> dict:
    start = stdout.find("{")
    blob = stdout[start:]
    depth = 0
    cut = "{}"
    for i, ch in enumerate(blob):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                cut = blob[: i + 1]
                break
    return json.loads(cut)


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
            self.assertIn("on_path", second.stdout)
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

    def test_install_copies_new_slash_commands_when_cursor_home_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            env["USERPROFILE"] = tmp
            home = Path(tmp)
            if os.name == "nt" and len(str(home)) >= 2 and str(home)[1] == ":":
                env["HOMEDRIVE"] = str(home)[:2]
                env["HOMEPATH"] = str(home)[2:] or "\\"
            env["SESSTALK_HOME"] = str(home / ".sesstalk")
            (home / ".cursor").mkdir()
            result = subprocess.run(
                [sys.executable, "-S", str(ROOT / "install.py"), "--no-mcp", "--no-hooks"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            commands = home / ".cursor" / "commands"
            for name in ("doctor.md", "init.md", "log.md", "schema.md"):
                self.assertTrue((commands / name).is_file(), name)
            skill = (home / ".cursor" / "skills" / "sesstalk" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("/doctor", skill)

    def test_install_detects_hermes_when_grok_home_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _isolated_env(tmp)
            home = Path(tmp)
            (home / ".hermes").mkdir()
            result = subprocess.run(
                [sys.executable, "-S", str(ROOT / "install.py"), "--no-mcp", "--no-hooks"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("hermes", result.stdout)
            self.assertIn("skip_reasons", result.stdout)
            payload = _first_json(result.stdout)
            self.assertIn("hermes", payload["configured"])
            self.assertIn("grok", payload["skipped"])
            self.assertTrue((home / ".hermes" / "skills" / "sesstalk" / "SKILL.md").is_file())
            self.assertTrue(any("hermes" in reason.lower() or "grok" in reason.lower() for reason in payload["skip_reasons"]))
            self.assertIn("warning", payload)

    @unittest.skipIf(sys.platform == "win32", "Unix PATH symlink")
    def test_install_symlinks_local_bin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _isolated_env(tmp)
            home = Path(tmp)
            result = subprocess.run(
                [sys.executable, "-S", str(ROOT / "install.py"), "--no-mcp", "--no-hooks"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            link = home / ".local" / "bin" / "sesstalk"
            self.assertTrue(link.exists(), result.stdout + result.stderr)
            payload = _first_json(result.stdout)
            self.assertIn("on_path", payload)
            self.assertFalse(payload["on_path"])
            self.assertIn("PATH", payload["warning"])
            self.assertIn("export PATH=", result.stderr)
