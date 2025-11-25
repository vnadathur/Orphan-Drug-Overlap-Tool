"""Centralized configuration for fuzzy match thresholds."""

from __future__ import annotations

from dataclasses import dataclass


def _clamp_percentage(value: int) -> int:
    """Keep percentages within [0, 100]."""
    return max(0, min(100, value))


@dataclass(frozen=True)
class MatchingThresholds:
    """All fuzzy matching thresholds derived from a single target percent."""

    base: int
    quick_compare_floor: int
    salt_check_floor: int
    component_match: int
    component_accept: int
    partial_combo_score_floor: int
    salt_gate: int
    high_gate: int
    medium_gate: int
    indication_loose: int
    indication_medium: int
    indication_strict: int
    indication_base: int
    missing_indication_floor: int
    combination_min_coverage: float


def build_thresholds(target_percent: int) -> MatchingThresholds:
    """Derive a coherent set of thresholds anchored on the selected percent."""
    base = _clamp_percentage(target_percent or 0)

    return MatchingThresholds(
        base=base,
        quick_compare_floor=_clamp_percentage(base - 15),  # mirrors historical 70
        salt_check_floor=_clamp_percentage(base - 5),  # mirrors historical 80
        component_match=_clamp_percentage(base + 5),  # mirrors historical 90
        component_accept=base,  # mirrors historical 85
        partial_combo_score_floor=_clamp_percentage(base - 5),  # mirrors historical ~80
        salt_gate=_clamp_percentage(base + 13),  # mirrors historical 98
        high_gate=_clamp_percentage(base + 10),  # mirrors historical 95
        medium_gate=_clamp_percentage(base + 5),  # mirrors historical 90
        indication_loose=_clamp_percentage(base - 45),  # mirrors historical 40
        indication_medium=_clamp_percentage(base - 35),  # mirrors historical 50
        indication_strict=_clamp_percentage(base - 20),  # mirrors historical 65
        indication_base=_clamp_percentage(base - 15),  # mirrors historical 70
        missing_indication_floor=_clamp_percentage(base + 10),  # mirrors historical 95
        combination_min_coverage=0.5,
    )

