#!/usr/bin/env python3
"""Install sesstalk CLI, skills, and slash commands into local agent homes."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"wrote {dest}")


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
    return dest_dir


def install_skill(dest: Path) -> None:
    if not dest.parent.exists() and dest.parent.name != "skills":
        # Only create skill dirs under known agent homes that already exist.
        return
    if not dest.parent.parent.exists():
        return
    copy_file(ROOT / "skills" / "SKILL.md", dest)


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


def main() -> None:
    install_cli()
    skill_src = ROOT / "skills" / "SKILL.md"
    if not skill_src.is_file():
        print("missing skills/SKILL.md", file=sys.stderr)
        raise SystemExit(1)

    for agent_home in (HOME / ".cursor", HOME / ".claude", HOME / ".codex", HOME / ".grok"):
        if agent_home.exists():
            dest = agent_home / "skills" / "sesstalk" / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy_file(skill_src, dest)

    if (HOME / ".cursor").exists():
        install_commands(HOME / ".cursor" / "commands")
    if (HOME / ".claude").exists():
        install_commands(HOME / ".claude" / "commands", claude=True)

    print("ok")


if __name__ == "__main__":
    main()
