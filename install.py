#!/usr/bin/env python3
"""Install sesstalk CLI, skills, slash commands, and optional MCP registration."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"wrote {dest}")


def python_path() -> str:
    return sys.executable


def hermes_home() -> Path:
    raw = os.environ.get("HERMES_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return HOME / ".hermes"


def sesstalk_on_path() -> bool:
    return shutil.which("sesstalk") is not None


def install_cli() -> Path:
    dest_dir = HOME / ".sesstalk"
    dest_dir.mkdir(parents=True, exist_ok=True)
    copy_file(ROOT / "sesstalk.py", dest_dir / "sesstalk.py")
    copy_file(ROOT / "sesstalk.cmd", dest_dir / "sesstalk.cmd")
    unix = dest_dir / "sesstalk"
    copy_file(ROOT / "sesstalk", unix)
    try:
        unix.chmod(unix.stat().st_mode | 0o111)
    except OSError:
        pass

    if sys.platform != "win32":
        local_bin = HOME / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        symlink = local_bin / "sesstalk"
        try:
            if symlink.exists() or symlink.is_symlink():
                symlink.unlink()
            symlink.symlink_to(unix)
            print(f"symlinked {symlink} -> {unix}")
        except OSError as exc:
            print(f"could not symlink to {local_bin}: {exc}", file=sys.stderr)

    if not sesstalk_on_path():
        if sys.platform == "win32":
            print(
                'sesstalk not on PATH; add %USERPROFILE%\\.sesstalk to PATH or call "%USERPROFILE%\\.sesstalk\\sesstalk.cmd"',
                file=sys.stderr,
            )
        else:
            print(
                'sesstalk not on PATH; export PATH="$HOME/.local/bin:$HOME/.sesstalk:$PATH"',
                file=sys.stderr,
            )
    return dest_dir


def install_commands(command_dir: Path, *, claude: bool = False) -> None:
    if not command_dir.parent.exists():
        return
    command_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "commands").glob("*.md")):
        text = src.read_text(encoding="utf-8")
        if claude and "allowed-tools:" not in text:
            text = text.replace("---\n", "---\nallowed-tools: [Bash]\n", 1)
        dest = command_dir / src.name
        dest.write_text(text, encoding="utf-8")
        print(f"wrote {dest}")


def mcp_server_block(cli_dir: Path) -> dict:
    return {
        "command": python_path(),
        "args": ["-S", str(cli_dir / "sesstalk.py"), "mcp"],
    }


def merge_json_mcp(path: Path, cli_dir: Path) -> bool:
    config: dict = {"mcpServers": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
        except json.JSONDecodeError:
            pass
    servers = config.setdefault("mcpServers", {})
    servers["sesstalk"] = mcp_server_block(cli_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return True


def merge_cursor_mcp(cli_dir: Path) -> bool:
    if not (HOME / ".cursor").exists():
        return False
    return merge_json_mcp(HOME / ".cursor" / "mcp.json", cli_dir)


def merge_claude_mcp(cli_dir: Path) -> bool:
    if not (HOME / ".claude").exists() and not (HOME / ".claude.json").exists():
        return False
    return merge_json_mcp(HOME / ".claude.json", cli_dir)


def merge_codex_mcp(cli_dir: Path) -> bool:
    codex_home = HOME / ".codex"
    if not codex_home.exists():
        return False
    path = codex_home / "config.toml"
    marker = "[mcp_servers.sesstalk]"
    block = (
        f"\n{marker}\n"
        f"command = {json.dumps(python_path())}\n"
        f"args = [{json.dumps('-S')}, {json.dumps(str(cli_dir / 'sesstalk.py'))}, {json.dumps('mcp')}]\n"
    )
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in existing:
        print(f"kept {path}")
        return True
    path.write_text(existing + block, encoding="utf-8")
    print(f"wrote {path}")
    return True


def hook_command_plain(cli_dir: Path, vendor: str) -> str:
    return f'"{python_path()}" -S "{cli_dir / "sesstalk.py"}" hook --vendor {vendor}'


def merge_cursor_hooks(cli_dir: Path) -> bool:
    if not (HOME / ".cursor").exists():
        return False
    path = HOME / ".cursor" / "hooks.json"
    config: dict = {"version": 1, "hooks": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
        except json.JSONDecodeError:
            pass
    hooks = config.setdefault("hooks", {})
    stops = list(hooks.get("stop") or [])
    cmd = hook_command_plain(cli_dir, "cursor")
    if not any(
        isinstance(item, dict) and "sesstalk.py" in str(item.get("command") or "") and "hook" in str(item.get("command") or "")
        for item in stops
    ):
        stops.append({"command": cmd, "loop_limit": 5})
        hooks["stop"] = stops
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    else:
        print(f"kept {path}")
    return True


def merge_claude_hooks(cli_dir: Path) -> bool:
    if not (HOME / ".claude").exists():
        return False
    path = HOME / ".claude" / "settings.json"
    config: dict = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
        except json.JSONDecodeError:
            pass
    hooks = config.setdefault("hooks", {})
    stops = list(hooks.get("Stop") or [])
    cmd = hook_command_plain(cli_dir, "claude")
    encoded = json.dumps(stops)
    if "sesstalk.py" in encoded and "hook" in encoded:
        print(f"kept {path}")
        return True
    stops.append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
    hooks["Stop"] = stops
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return True


def merge_codex_hooks(cli_dir: Path) -> bool:
    if not (HOME / ".codex").exists():
        return False
    path = HOME / ".codex" / "hooks.json"
    config: dict = {"hooks": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
        except json.JSONDecodeError:
            pass
    hooks = config.setdefault("hooks", {})
    stops = list(hooks.get("Stop") or [])
    cmd = hook_command_plain(cli_dir, "codex")
    encoded = json.dumps(stops)
    if "sesstalk.py" in encoded and "hook" in encoded:
        print(f"kept {path}")
        return True
    stops.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": cmd,
                    "timeout": 10,
                    "statusMessage": "sesstalk unread?",
                }
            ]
        }
    )
    hooks["Stop"] = stops
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return True


def verify_mailbox(cli_py: Path) -> None:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="sesstalk-verify-") as tmp:
        env = os.environ.copy()
        env["SESSTALK_HOME"] = tmp
        send = subprocess.run(
            [python_path(), "-S", str(cli_py), "send", "--from", "verify-a", "--to", "verify-b", "ping"],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        recv = subprocess.run(
            [python_path(), "-S", str(cli_py), "receive", "--name", "verify-b", "--timeout", "5"],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        payload = json.loads(recv.stdout)
        if payload.get("message", {}).get("text") != "ping":
            raise SystemExit("verify failed: unexpected receive payload")
        print("verify mailbox: ok")
        print(send.stdout.strip())


def doctor(
    cli_dir: Path,
    mcp_registered: dict[str, bool],
    hooks_registered: dict[str, bool],
    configured: list[str],
    skipped: list[str],
    skip_reasons: list[str],
) -> None:
    on_path = sesstalk_on_path()
    payload = {
        "python": python_path(),
        "home": str(HOME / ".sesstalk"),
        "cli": str(cli_dir / "sesstalk.py"),
        "on_path": on_path,
        "mcp_registered": any(mcp_registered.values()),
        "mcp": mcp_registered,
        "hooks": hooks_registered,
        "configured": configured,
        "skipped": skipped,
        "skip_reasons": skip_reasons,
        "hosts": {
            "cursor": (HOME / ".cursor").exists(),
            "claude": (HOME / ".claude").exists() or (HOME / ".claude.json").exists(),
            "codex": (HOME / ".codex").exists(),
            "grok": (HOME / ".grok").exists(),
            "hermes": hermes_home().exists(),
        },
        "deprecated_agent_bus": str(HOME / ".agent-bus"),
        "writes_agent_bus": False,
        "note": "~/.agent-bus is deprecated; sesstalk never writes there",
    }
    warnings: list[str] = []
    if not on_path:
        if sys.platform == "win32":
            warnings.append(
                r'sesstalk not on PATH; add %USERPROFILE%\.sesstalk to PATH or call "%USERPROFILE%\.sesstalk\sesstalk.cmd"'
            )
        else:
            warnings.append(
                'sesstalk not on PATH; export PATH="$HOME/.local/bin:$HOME/.sesstalk:$PATH"'
            )
    if "hermes" in configured and "grok" in skipped:
        warnings.append(
            "Hermes host configured; Grok/Hermes cannot wake an idle peer — keep /receive open"
        )
    if warnings:
        payload["warning"] = "; ".join(warnings)
    print(json.dumps(payload, indent=2))
    print(
        "doctor: python={python} home={home} on_path={on_path} mcp={mcp}".format(
            python=payload["python"],
            home=payload["home"],
            on_path=on_path,
            mcp=payload["mcp_registered"],
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Install sesstalk")
    parser.add_argument("--verify", action="store_true", help="Smoke send/receive after install")
    parser.add_argument("--no-mcp", action="store_true", help="Do not register Cursor MCP")
    parser.add_argument("--no-hooks", action="store_true", help="Do not register Stop/stop hooks")
    args = parser.parse_args()

    skill_src = ROOT / "skills" / "SKILL.md"
    if not skill_src.is_file():
        print("missing skills/SKILL.md", file=sys.stderr)
        raise SystemExit(1)

    cli_dir = install_cli()
    configured = []
    skipped = []
    skip_reasons: list[str] = []
    for agent_home, label in (
        (HOME / ".cursor", "cursor"),
        (HOME / ".claude", "claude"),
        (HOME / ".codex", "codex"),
        (HOME / ".grok", "grok"),
        (hermes_home(), "hermes"),
    ):
        if agent_home.exists():
            dest = agent_home / "skills" / "sesstalk" / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy_file(skill_src, dest)
            configured.append(label)
        else:
            skipped.append(label)
            if label == "hermes":
                skip_reasons.append(f"hermes skipped ({agent_home} missing)")
            elif label == "grok":
                skip_reasons.append("grok skipped (~/.grok missing)")

    if "grok" in skipped and "hermes" in configured:
        skip_reasons.append("Hermes is the grok-side host; keep /receive open (no wake API)")
    elif "grok" in skipped and "hermes" in skipped:
        skip_reasons.append("no grok/hermes host (~/.grok and ~/.hermes missing)")

    if (HOME / ".cursor").exists():
        install_commands(HOME / ".cursor" / "commands")
    if (HOME / ".claude").exists():
        install_commands(HOME / ".claude" / "commands", claude=True)

    mcp_registered = {"cursor": False, "claude": False, "codex": False}
    if not args.no_mcp:
        mcp_registered["cursor"] = merge_cursor_mcp(cli_dir)
        mcp_registered["claude"] = merge_claude_mcp(cli_dir)
        mcp_registered["codex"] = merge_codex_mcp(cli_dir)

    hooks_registered = {"cursor": False, "claude": False, "codex": False}
    if not args.no_hooks:
        hooks_registered["cursor"] = merge_cursor_hooks(cli_dir)
        hooks_registered["claude"] = merge_claude_hooks(cli_dir)
        hooks_registered["codex"] = merge_codex_hooks(cli_dir)

    print("configured:", ", ".join(configured) or "(none)")
    print("skipped:", ", ".join(skipped) or "(none)")
    if skip_reasons:
        print("skip_reasons:", "; ".join(skip_reasons))
    print("deprecated ~/.agent-bus is unused; installer does not write there")
    doctor(cli_dir, mcp_registered, hooks_registered, configured, skipped, skip_reasons)
    if args.verify:
        verify_mailbox(cli_dir / "sesstalk.py")
        if not sesstalk_on_path():
            if sys.platform == "win32":
                print(
                    'verify PATH: sesstalk not resolvable; add %USERPROFILE%\\.sesstalk to PATH',
                    file=sys.stderr,
                )
            else:
                print(
                    'verify PATH: sesstalk not resolvable; export PATH="$HOME/.local/bin:$HOME/.sesstalk:$PATH"',
                    file=sys.stderr,
                )
    print("ok")


if __name__ == "__main__":
    main()
