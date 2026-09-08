"""Timestore uniqueness quantum + diurnal/year helpers."""

from __future__ import annotations

from datetime import datetime, timezone

TIME_QUANTUM_S = 0.0006
YEAR_SECONDS = 365.25 * 24 * 3600


def quantize_posix(ts: float, quantum: float = TIME_QUANTUM_S) -> float:
    """Round POSIX seconds to uniqueness quantum (default 0.0006)."""
    if quantum <= 0:
        return float(ts)
    return round(float(ts) / quantum) * quantum


def circle_fraction_utc(ts: float | None = None) -> float:
    """Fraction through the UTC day in [0, 1)."""
    if ts is None:
        ts = datetime.now(timezone.utc).timestamp()
    day = 24 * 3600
    return (float(ts) % day) / day


def within_year_horizon(ts: float, *, now: float | None = None) -> bool:
    """True if ts is in [now, now+1y] (inclusive start)."""
    if now is None:
        now = datetime.now(timezone.utc).timestamp()
    return float(now) <= float(ts) <= float(now) + YEAR_SECONDS
