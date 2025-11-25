"""Simple CLI progress utilities for pipeline transparency."""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class CLIProgressBar:
    """Render a consistent progress bar for long-running loops."""

    total: int
    label: str = "Progress"
    bar_length: int = 40

    def __post_init__(self) -> None:
        self._effective_total = self.total if self.total > 0 else 1
        self._current = 0
        self._has_output = False

    def advance(self, step: int = 1) -> None:
        """Increment progress by `step` units."""
        self.update(self._current + step)

    def update(self, value: int) -> None:
        """Render the bar at an arbitrary absolute value."""
        self._current = max(0, min(value, self._effective_total))
        filled = int(self.bar_length * self._current / self._effective_total)
        bar = '#' * filled + '-' * (self.bar_length - filled)
        percent = (self._current / self._effective_total) * 100
        sys.stdout.write(f"\r  {self.label:<28} [{bar}] {percent:5.1f}%")
        sys.stdout.flush()
        self._has_output = True

    def complete(self) -> None:
        """Ensure the bar finishes at 100% and break the line."""
        if self.total <= 0 and not self._has_output:
            sys.stdout.write(f"  {self.label:<28} [{'-' * self.bar_length}]   0.0%\n")
            sys.stdout.flush()
            return

        self.update(self._effective_total)
        sys.stdout.write('\n')
        sys.stdout.flush()

