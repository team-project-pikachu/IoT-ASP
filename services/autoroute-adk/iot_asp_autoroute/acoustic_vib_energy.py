"""Acoustic vib hop-band energy burst (#5) — Python twin of public/acoustic-vib-energy.js.

Keep WINDOW_MS / MARGIN_DB / prefer_energy / rolling-median math in sync with the
JS module (tests assert parity). DeviceMotion (#4) and material arming UI (#6)
are out of scope here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List, Optional, Sequence, Tuple

WINDOW_MS = 1000
MARGIN_DB = 12.0
SILENCE_DB = -90.0
SILENCE_HOLD_MS = 800


def median_of(values: Sequence[float]) -> float:
    if not values:
        return -120.0
    sorted_vals = sorted(float(v) for v in values)
    mid = (len(sorted_vals) - 1) / 2.0
    lo = sorted_vals[math.floor(mid)]
    hi = sorted_vals[math.ceil(mid)]
    return (lo + hi) / 2.0


def prefer_energy(energy_db: float, mic_diff_db: Optional[float] = None) -> float:
    """Prefer micDiff when finite and above floor; else raw mic/spectrum energy."""
    if mic_diff_db is not None:
        try:
            md = float(mic_diff_db)
        except (TypeError, ValueError):
            md = None
        else:
            if md == md and md > -119:  # finite
                return md
    try:
        e = float(energy_db)
    except (TypeError, ValueError):
        return -120.0
    if e != e:  # NaN
        return -120.0
    return e


@dataclass
class AcousticVibTracker:
    window_ms: float = WINDOW_MS
    margin_db: float = MARGIN_DB
    silence_db: float = SILENCE_DB
    silence_hold_ms: float = SILENCE_HOLD_MS
    _samples: List[Tuple[float, float]] = field(default_factory=list)
    _burst_active: bool = False
    _silence_since: Optional[float] = None
    _last_t: float = 0.0

    def reset(self) -> None:
        self._samples.clear()
        self._burst_active = False
        self._silence_since = None
        self._last_t = 0.0

    def _prune(self, t_ms: float) -> None:
        cutoff = t_ms - self.window_ms
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.pop(0)

    def push(self, energy_db: float, t_ms: Optional[float] = None) -> dict:
        t = float(t_ms) if t_ms is not None else self._last_t
        self._last_t = t
        try:
            e = float(energy_db)
        except (TypeError, ValueError):
            e = -120.0
        if e != e:
            e = -120.0
        self._samples.append((t, e))
        self._prune(t)

        median = median_of([s[1] for s in self._samples])
        delta = e - median
        rising = delta >= self.margin_db and e > self.silence_db

        if e <= self.silence_db or delta < 3:
            if self._silence_since is None:
                self._silence_since = t
        else:
            self._silence_since = None
        silence = (
            self._silence_since is not None
            and (t - self._silence_since) >= self.silence_hold_ms
        )

        if rising:
            self._burst_active = True
        elif silence or delta < self.margin_db * 0.4:
            self._burst_active = False

        return {
            "energy": e,
            "median": round(median, 1),
            "delta": round(delta, 1),
            "burst": bool(self._burst_active),
            "rising": bool(rising),
            "silence": bool(silence),
            "n": len(self._samples),
        }

    def snapshot(self) -> dict:
        median = median_of([s[1] for s in self._samples])
        return {
            "median": round(median, 1),
            "burst": bool(self._burst_active),
            "n": len(self._samples),
            "windowMs": self.window_ms,
            "marginDb": self.margin_db,
        }


def create_tracker(**kwargs: float) -> AcousticVibTracker:
    return AcousticVibTracker(**kwargs)
