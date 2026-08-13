#!/usr/bin/env python3
"""Regenerate docs/demo.{txt,svg,cast} from `sesstalk demo`. No LLM."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.sax.saxutils
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "sesstalk.py"


def run_demo() -> str:
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, "-S", str(CLI), "demo"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout


def write_cast(text: str, path: Path, width: int = 88, height: int = 32) -> None:
    header = {"version": 2, "width": width, "height": height, "title": "sesstalk demo"}
    lines = [json.dumps(header)]
    t = 0.05
    for line in text.splitlines(True):
        chunk = line if line.endswith("\n") else line + "\n"
        lines.append(json.dumps([round(t, 3), "o", chunk]))
        t += 0.04
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def line_fill(row: str) -> str:
    stripped = row.strip()
    if stripped.startswith("sesstalk") or stripped.startswith("$"):
        return "#E6C07B"
    if stripped.startswith("Next:"):
        return "#E07A5F"
    if stripped.startswith('"') or stripped in {"{", "}", "[", "]", "},", "],"}:
        return "#A3BE8C"
    if stripped.startswith("--") or " --" in row:
        return "#81A1C1"
    return "#D8D0C4"


def write_svg(text: str, path: Path) -> None:
    rows = text.splitlines() or [""]
    width = 920
    line_h = 18
    pad = 28
    height = pad * 2 + 20 + line_h * len(rows)
    parts = []
    y = pad + 36
    for row in rows:
        esc = xml.sax.saxutils.escape(row.replace("\t", "    "))
        fill = line_fill(row)
        parts.append(
            f'<text x="20" y="{y}" fill="{fill}" '
            f'font-family="ui-monospace, SFMono-Regular, Consolas, monospace" '
            f'font-size="13">{esc}</text>'
        )
        y += line_h
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="sesstalk demo terminal">\n'
        '  <rect width="100%" height="100%" rx="8" fill="#1c1917"/>\n'
        '  <circle cx="22" cy="18" r="5" fill="#c45c4a"/>\n'
        '  <circle cx="40" cy="18" r="5" fill="#c4a35a"/>\n'
        '  <circle cx="58" cy="18" r="5" fill="#6a8f71"/>\n'
        '  <text x="80" y="22" fill="#a8a29a" font-family="ui-monospace, Consolas, monospace" '
        'font-size="12">sesstalk demo</text>\n'
        f'  {"".join(parts)}\n'
        "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Record sesstalk demo without an LLM")
    parser.add_argument("--out", default=str(ROOT / "docs"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    text = run_demo()
    (out / "demo.txt").write_text(text, encoding="utf-8")
    write_svg(text, out / "demo.svg")
    write_cast(text, out / "demo.cast")
    print(f"wrote {out / 'demo.txt'}", flush=True)


if __name__ == "__main__":
    main()
