"""Gemeinsame Fixtures: das Handbeispiel (von Hand durchgerechnet, DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lks_scenario as S  # noqa: E402


@pytest.fixture
def hand():
    """Handbeispiel: fünf Variablen, sieben Klauseln, neun Modelle; Seed 20 löst es in drei Umdrehungen (Handrechnung in test_algorithm.py)."""
    return S.hand_formel()
