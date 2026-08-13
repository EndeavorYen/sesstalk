#!/usr/bin/env python3
"""Regenerate README diagrams. Zinc + lime HUD — valid XML, no serif fallback."""

from __future__ import annotations

import argparse
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"

BG = "#09090B"
PANEL = "#111114"
LINE = "#27272A"
GRID = "#18181B"
TEXT = "#FAFAFA"
MUTED = "#A1A1AA"
DIM = "#71717A"
ACCENT = "#C6FF4A"
INK = "#09090B"
FONT = "ui-sans-serif, Segoe UI, Helvetica Neue, Arial, sans-serif"
MONO = "ui-monospace, Cascadia Mono, SF Mono, Consolas, monospace"


def attr(**kwargs: object) -> str:
    parts = []
    for key, value in kwargs.items():
        if value is None:
            continue
        name = key.replace("_", "-")
        if name == "cls":
            name = "class"
        parts.append(f" {name}={quoteattr(str(value))}")
    return "".join(parts)


def text(x: float, y: float, body: str, **kwargs: object) -> str:
    return f"<text{attr(x=x, y=y, **kwargs)}>{escape(body)}</text>"


def rect(**kwargs: object) -> str:
    return f"<rect{attr(**kwargs)}/>"


def circle(**kwargs: object) -> str:
    return f"<circle{attr(**kwargs)}/>"


def path_d(d: str, **kwargs: object) -> str:
    return f"<path{attr(d=d, **kwargs)}/>"


def frame(width: int, height: int, label: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label={quoteattr(label)}>
  <defs>
    <pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="0.85" fill="{GRID}"/>
    </pattern>
  </defs>
  {rect(width=width, height=height, fill=BG)}
  {rect(width=width, height=height, fill="url(#dots)")}
  {rect(x=0, y=0, width=width, height=3, fill=ACCENT)}
  {body}
</svg>
"""


def wordmark(title: str, subtitle: str) -> str:
    return text(
        40,
        28,
        title,
        fill=TEXT,
        font_family=FONT,
        font_size=12,
        font_weight=600,
        letter_spacing="0.34em",
    ) + text(40, 48, subtitle, fill=DIM, font_family=FONT, font_size=13)


def architecture_svg() -> str:
    left = f"""
  <g transform="translate(40,70)">
    {rect(width=332, height=318, rx=18, fill=PANEL, stroke=LINE, stroke_width=1)}
    {rect(x=0, y=0, width=4, height=318, rx=2, fill=ACCENT)}
    {text(28, 36, "01  SESSION", fill=DIM, font_family=FONT, font_size=11, letter_spacing="0.18em")}
    {text(28, 78, "cursor-a", fill=TEXT, font_family=FONT, font_size=28, font_weight=600)}
    {text(28, 128, "/send claude,codex", fill=MUTED, font_family=MONO, font_size=13)}
    {text(28, 152, "--goal ship auth", fill=ACCENT, font_family=MONO, font_size=13)}
    {text(28, 176, "--thread auth-review", fill=MUTED, font_family=MONO, font_size=13)}
    {text(28, 236, "Hands a work object.", fill=DIM, font_family=FONT, font_size=14)}
    {text(28, 260, "Does not wake a prompt.", fill=DIM, font_family=FONT, font_size=14)}
  </g>
"""
    mid = f"""
  <g transform="translate(396,70)">
    {rect(width=248, height=318, rx=18, fill=ACCENT)}
    {text(22, 36, "MAILBOX", fill=INK, font_family=FONT, font_size=11, font_weight=600, letter_spacing="0.22em")}
    {text(22, 72, "JSONL", fill=INK, font_family=FONT, font_size=28, font_weight=700)}
    {text(22, 96, "~/.sesstalk", fill="#3F6212", font_family=MONO, font_size=12)}
    {rect(x=16, y=118, width=216, height=132, rx=12, fill=INK)}
    {text(28, 146, 'to: claude + codex', fill=ACCENT, font_family=MONO, font_size=12)}
    {text(28, 168, "thread: auth-review", fill=TEXT, font_family=MONO, font_size=12)}
    {text(28, 190, "goal: ship auth", fill=MUTED, font_family=MONO, font_size=12)}
    {text(28, 212, "untrusted · depth 0", fill=MUTED, font_family=MONO, font_size=12)}
    {text(28, 234, "delivery ≠ attention", fill=ACCENT, font_family=MONO, font_size=12)}
    {text(22, 278, "same machine", fill=INK, font_family=FONT, font_size=13)}
    {text(22, 300, "one OS user", fill="#3F6212", font_family=FONT, font_size=13)}
  </g>
"""
    right = f"""
  <g transform="translate(668,70)">
    {rect(width=332, height=318, rx=18, fill=PANEL, stroke=LINE, stroke_width=1)}
    {rect(x=328, y=0, width=4, height=318, rx=2, fill=ACCENT)}
    {text(28, 36, "02  SESSION", fill=DIM, font_family=FONT, font_size=11, letter_spacing="0.18em")}
    {text(28, 78, "claude", fill=TEXT, font_family=FONT, font_size=28, font_weight=600)}
    {text(28, 128, "/receive", fill=MUTED, font_family=MONO, font_size=13)}
    {text(28, 152, "/reply looks good", fill=ACCENT, font_family=MONO, font_size=13)}
    {text(28, 236, "Starts a turn — or", fill=DIM, font_family=FONT, font_size=14)}
    {text(28, 260, "idle_no_adapter", fill=TEXT, font_family=MONO, font_size=14)}
    {text(28, 284, "Never a fake read.", fill=DIM, font_family=FONT, font_size=14)}
  </g>
"""
    arrows = (
        path_d("M372 229 H392", stroke=ACCENT, stroke_width=2, fill="none")
        + f'<polygon points="392,224 404,229 392,234" fill="{ACCENT}"/>'
        + path_d("M644 229 H664", stroke=ACCENT, stroke_width=2, fill="none")
        + f'<polygon points="664,224 676,229 664,234" fill="{ACCENT}"/>'
    )
    body = wordmark("SESSTALK", "local mailbox · not a chat product") + left + arrows + mid + right
    return frame(1040, 420, "sesstalk: cursor-a sends a JSONL work object to claude on one machine", body)


def envelope_svg() -> str:
    fields = [
        ("goal", "What done looks like"),
        ("next", "The one step after this"),
        ("files", "Paths you may touch"),
        ("thread", "Shared id, e.g. auth-review"),
        ("audience", "claude, codex — one object"),
        ("provenance", "peer · untrusted · depth"),
    ]
    rows = []
    for i, (key, hint) in enumerate(fields):
        y = 108 + i * 40
        if i:
            rows.append(path_d(f"M56 {y - 22} H984", stroke=LINE, stroke_width=1))
        rows.append(
            text(56, y, key, fill=ACCENT, font_family=MONO, font_size=15)
            + text(240, y, hint, fill=MUTED, font_family=FONT, font_size=15)
        )
    body = (
        wordmark("WORK ENVELOPE", "one object · many inboxes · inbound is not the human")
        + rect(x=40, y=64, width=960, height=292, rx=18, fill=PANEL, stroke=LINE, stroke_width=1)
        + "".join(rows)
    )
    return frame(1040, 380, "sesstalk work envelope fields", body)


def attention_svg() -> str:
    items = [
        ("#4ADE80", "listening", "On /receive now"),
        ("#C6FF4A", "started_turn", "Adapter woke a turn"),
        ("#FBBF24", "hook_armed", "Stop hook may continue"),
        ("#FB7185", "idle_no_adapter", "Queued — read blocker"),
        ("#A1A1AA", "error", "Adapter ran and failed"),
    ]
    rows = []
    for i, (dot, name, hint) in enumerate(items):
        y = 86 + i * 50
        rows.append(
            rect(x=56, y=y - 22, width=928, height=44, rx=12, fill="#0C0C0E")
            + circle(cx=80, cy=y, r=6, fill=dot)
            + text(104, y + 5, name, fill=TEXT, font_family=MONO, font_size=14)
            + text(340, y + 5, hint, fill=MUTED, font_family=FONT, font_size=14)
        )
    body = (
        wordmark("NUDGE IS HONEST", "send queues · nudge may wake · never a fake receipt")
        + rect(x=40, y=64, width=960, height=276, rx=18, fill=PANEL, stroke=LINE, stroke_width=1)
        + "".join(rows)
    )
    return frame(1040, 360, "sesstalk nudge attention states", body)


def flow_svg() -> str:
    cols = [
        ("SEND", "queues JSONL", "Does not start a turn."),
        ("RECEIVE", "worker is listening", "Mail becomes this turn."),
        ("NUDGE", "best-effort wake", "idle_no_adapter is honest."),
    ]
    cards = []
    for i, (title, line, note) in enumerate(cols):
        x = 40 + i * 333
        cards.append(
            f'<g transform="translate({x},70)">'
            + rect(width=313, height=190, rx=18, fill=PANEL, stroke=LINE, stroke_width=1)
            + rect(x=24, y=24, width=36, height=3, rx=1.5, fill=ACCENT)
            + text(24, 64, title, fill=TEXT, font_family=FONT, font_size=22, font_weight=600, letter_spacing="0.12em")
            + text(24, 104, line, fill=ACCENT, font_family=MONO, font_size=14)
            + text(24, 148, note, fill=MUTED, font_family=FONT, font_size=14)
            + "</g>"
        )
    body = wordmark("DELIVERY ≠ ATTENTION", "three verbs · one machine") + "".join(cards)
    return frame(1040, 292, "sesstalk send queues, receive listens, nudge may wake", body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render README SVGs")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    files = {
        "architecture.svg": architecture_svg(),
        "envelope.svg": envelope_svg(),
        "attention.svg": attention_svg(),
        "flow.svg": flow_svg(),
    }
    for name, blob in files.items():
        (dest / name).write_text(blob, encoding="utf-8", newline="\n")
        print(f"wrote {dest / name}", flush=True)


if __name__ == "__main__":
    main()
