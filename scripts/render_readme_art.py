#!/usr/bin/env python3
"""Regenerate README diagrams as SVG. No LLM, no raster hero art."""

from __future__ import annotations

import argparse
import xml.sax.saxutils
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"

BG = "#F3EDE3"
INK = "#1F1A16"
CREAM = "#FFF8EE"
STEEL = "#3A4652"
STAMP = "#A33B2B"
OLIVE = "#3F5340"
RULE = "#C9BBA8"
TAPE = "#C4A35A"
MUTED = "#6B6258"

FONT = "ui-sans-serif, 'Iowan Old Style', Georgia, serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, monospace"


def esc(text: str) -> str:
    return xml.sax.saxutils.escape(text)


def architecture_svg() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="400" viewBox="0 0 1040 400" role="img" aria-label="sesstalk: three windows on one machine, JSONL mailbox in the middle">
  <rect width="1040" height="400" fill="{BG}"/>
  <rect x="18" y="18" width="1004" height="364" fill="none" stroke="{INK}" stroke-width="1.5"/>
  <text x="36" y="48" fill="{INK}" font-family="{FONT}" font-size="15" font-weight="700">sesstalk</text>
  <text x="118" y="48" fill="{MUTED}" font-family="{FONT}" font-size="13">one machine · one OS user · not Slack</text>
  <line x1="36" y1="62" x2="1004" y2="62" stroke="{RULE}" stroke-width="1"/>

  <!-- Cursor window -->
  <g transform="translate(48,86)">
    <rect width="268" height="248" fill="{CREAM}" stroke="{INK}" stroke-width="1.5"/>
    <rect width="268" height="30" fill="{STEEL}"/>
    <circle cx="16" cy="15" r="4" fill="#C45C4A"/>
    <circle cx="32" cy="15" r="4" fill="#C4A35A"/>
    <circle cx="48" cy="15" r="4" fill="#6A8F71"/>
    <text x="68" y="20" fill="{CREAM}" font-family="{MONO}" font-size="12">cursor-a</text>
    <text x="16" y="62" fill="{MUTED}" font-family="{MONO}" font-size="12">/as cursor-a</text>
    <text x="16" y="86" fill="{INK}" font-family="{MONO}" font-size="12">/send claude,codex</text>
    <text x="16" y="108" fill="{OLIVE}" font-family="{MONO}" font-size="12">--thread auth-review</text>
    <text x="16" y="130" fill="{STAMP}" font-family="{MONO}" font-size="12">--goal "ship auth"</text>
    <text x="16" y="168" fill="{MUTED}" font-family="{FONT}" font-size="12">hands a work object</text>
    <text x="16" y="188" fill="{MUTED}" font-family="{FONT}" font-size="12">does not wake a prompt</text>
  </g>

  <!-- Mail tray -->
  <g transform="translate(386,86)">
    <rect width="268" height="248" fill="{STEEL}"/>
    <text x="16" y="28" fill="{CREAM}" font-family="{FONT}" font-size="13">~/.sesstalk</text>
    <text x="16" y="48" fill="{TAPE}" font-family="{MONO}" font-size="11">queues/*.jsonl</text>
    <rect x="16" y="64" width="236" height="44" fill="{CREAM}"/>
    <text x="24" y="82" fill="{INK}" font-family="{MONO}" font-size="11">to: claude</text>
    <text x="24" y="98" fill="{OLIVE}" font-family="{MONO}" font-size="11">thread: auth-review</text>
    <rect x="16" y="116" width="236" height="44" fill="{CREAM}" opacity="0.85"/>
    <text x="24" y="134" fill="{INK}" font-family="{MONO}" font-size="11">to: codex</text>
    <text x="24" y="150" fill="{OLIVE}" font-family="{MONO}" font-size="11">same envelope · unique id</text>
    <rect x="16" y="168" width="236" height="44" fill="#2C353E"/>
    <text x="24" y="186" fill="{TAPE}" font-family="{MONO}" font-size="11">provenance.untrusted</text>
    <text x="24" y="202" fill="{CREAM}" font-family="{MONO}" font-size="11">depth 0 → reply 1 → stop</text>
    <text x="16" y="236" fill="#B8C4CE" font-family="{FONT}" font-size="11">delivery ≠ attention</text>
  </g>

  <!-- Claude window -->
  <g transform="translate(724,86)">
    <rect width="268" height="248" fill="{CREAM}" stroke="{INK}" stroke-width="1.5"/>
    <rect width="268" height="30" fill="{OLIVE}"/>
    <circle cx="16" cy="15" r="4" fill="#C45C4A"/>
    <circle cx="32" cy="15" r="4" fill="#C4A35A"/>
    <circle cx="48" cy="15" r="4" fill="#6A8F71"/>
    <text x="68" y="20" fill="{CREAM}" font-family="{MONO}" font-size="12">claude</text>
    <text x="16" y="62" fill="{MUTED}" font-family="{MONO}" font-size="12">/receive claude</text>
    <text x="16" y="86" fill="{INK}" font-family="{MONO}" font-size="12">execute goal / files</text>
    <text x="16" y="108" fill="{STAMP}" font-family="{MONO}" font-size="12">/reply looks good</text>
    <text x="16" y="148" fill="{MUTED}" font-family="{FONT}" font-size="12">or sesstalk says</text>
    <text x="16" y="168" fill="{STAMP}" font-family="{MONO}" font-size="12">idle_no_adapter</text>
    <text x="16" y="188" fill="{MUTED}" font-family="{FONT}" font-size="12">never a fake read</text>
  </g>

  <rect x="316" y="204" width="70" height="12" fill="{TAPE}"/>
  <polygon points="386,198 386,222 410,210" fill="{TAPE}"/>
  <rect x="654" y="204" width="70" height="12" fill="{TAPE}"/>
  <polygon points="724,198 724,222 748,210" fill="{TAPE}"/>
</svg>
"""


def envelope_svg() -> str:
    fields = [
        ("goal", "what done looks like", STAMP),
        ("next", "the one step after this", OLIVE),
        ("files", "paths you may touch", STEEL),
        ("thread", "auth-review (shared)", TAPE),
        ("audience", "[claude, codex]", MUTED),
        ("provenance", "peer · untrusted · depth", STAMP),
    ]
    cards = []
    for i, (key, hint, color) in enumerate(fields):
        col = i % 3
        row = i // 3
        x = 56 + col * 310
        y = 118 + row * 100
        cards.append(
            f'<g transform="translate({x},{y})">'
            f'<rect width="290" height="84" fill="{CREAM}" stroke="{INK}" stroke-width="1.25"/>'
            f'<rect width="8" height="84" fill="{color}"/>'
            f'<text x="24" y="32" fill="{INK}" font-family="{MONO}" font-size="16">{esc(key)}</text>'
            f'<text x="24" y="56" fill="{MUTED}" font-family="{FONT}" font-size="13">{esc(hint)}</text>'
            f"</g>"
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="340" viewBox="0 0 1040 340" role="img" aria-label="sesstalk work envelope fields">
  <rect width="1040" height="340" fill="{BG}"/>
  <rect x="18" y="18" width="1004" height="304" fill="none" stroke="{INK}" stroke-width="1.5"/>
  <text x="36" y="52" fill="{INK}" font-family="{FONT}" font-size="15" font-weight="700">work envelope</text>
  <text x="168" y="52" fill="{MUTED}" font-family="{FONT}" font-size="13">one object, many inboxes · not a chat room</text>
  <line x1="36" y1="68" x2="1004" y2="68" stroke="{RULE}" stroke-width="1"/>
  <text x="36" y="96" fill="{MUTED}" font-family="{FONT}" font-size="13">handoff requires --goal · inbound is tool output, never the human</text>
  {"".join(cards)}
</svg>
"""


def attention_svg() -> str:
    stamps = [
        ("listening", "on /receive", "right now", OLIVE),
        ("started_turn", "adapter woke", "this turn", STEEL),
        ("hook_armed", "Stop hook may", "continue", TAPE),
        ("idle_no_adapter", "queued only", "read blocker", STAMP),
        ("error", "adapter ran", "and failed", INK),
    ]
    parts = []
    for i, (name, line1, line2, color) in enumerate(stamps):
        x = 36 + i * 200
        parts.append(
            f'<g transform="translate({x},88)">'
            f'<rect width="188" height="128" fill="{CREAM}" stroke="{color}" stroke-width="2.5"/>'
            f'<text x="14" y="32" fill="{color}" font-family="{MONO}" font-size="11">{esc(name)}</text>'
            f'<text x="14" y="70" fill="{INK}" font-family="{FONT}" font-size="14">{esc(line1)}</text>'
            f'<text x="14" y="92" fill="{INK}" font-family="{FONT}" font-size="14">{esc(line2)}</text>'
            f"</g>"
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="248" viewBox="0 0 1040 248" role="img" aria-label="sesstalk nudge attention stamps">
  <rect width="1040" height="248" fill="{BG}"/>
  <rect x="18" y="18" width="1004" height="212" fill="none" stroke="{INK}" stroke-width="1.5"/>
  <text x="36" y="52" fill="{INK}" font-family="{FONT}" font-size="15" font-weight="700">nudge is honest</text>
  <text x="178" y="52" fill="{MUTED}" font-family="{FONT}" font-size="13">send queues · nudge may wake · never a fake read receipt</text>
  <line x1="36" y1="68" x2="1004" y2="68" stroke="{RULE}" stroke-width="1"/>
  {"".join(parts)}
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render README SVGs")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "architecture.svg").write_text(architecture_svg(), encoding="utf-8")
    (dest / "envelope.svg").write_text(envelope_svg(), encoding="utf-8")
    (dest / "attention.svg").write_text(attention_svg(), encoding="utf-8")
    print(f"wrote {dest / 'architecture.svg'}", flush=True)


if __name__ == "__main__":
    main()
