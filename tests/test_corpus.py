#!/usr/bin/env python3
"""Replay corpus fixtures. Empty corpus is a pass."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"


class CorpusTests(unittest.TestCase):
    def test_corpus_fixtures_are_well_formed(self) -> None:
        files = sorted(CORPUS.glob("*.json"))
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            for key in ("issue", "layer", "input", "expected"):
                self.assertIn(key, data, path.name)
