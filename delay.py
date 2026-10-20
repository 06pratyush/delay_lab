"""The look-back buffer: 'where was the nose D ms ago?'"""

from __future__ import annotations

from collections import deque

import numpy as np

MAX_DELAY_MS = 150


class DelayBuffer:
    """Time-stamped positions; answers queries for any past moment by blending neighbours."""

    def __init__(self, keep_ms: float = 1000.0):
        self.keep_ms = keep_ms
        self._samples: deque[tuple[float, np.ndarray]] = deque()

    def push(self, t_ms: float, xy) -> None:
        self._samples.append((t_ms, np.asarray(xy, dtype=float)))
        while self._samples and t_ms - self._samples[0][0] > self.keep_ms:
            self._samples.popleft()

    def clear(self) -> None:
        self._samples.clear()

    def __len__(self) -> int:
        return len(self._samples)

    def at(self, t_ms: float) -> np.ndarray | None:
        """Position at time t_ms, linearly blended; clamped to the oldest/newest sample."""
        if not self._samples:
            return None
        oldest, newest = self._samples[0], self._samples[-1]
        if t_ms <= oldest[0]:
            return oldest[1].copy()
        if t_ms >= newest[0]:
            return newest[1].copy()
        # Walk back from the newest sample: queries are at most ~150 ms old.
        later = newest
        for earlier in reversed(self._samples):
            if earlier[0] <= t_ms:
                break
            later = earlier
        (t0, p0), (t1, p1) = earlier, later
        return p0 + (t_ms - t0) / (t1 - t0) * (p1 - p0)

    def frame_interval_ms(self, default: float = 1000 / 30) -> float:
        """Typical time between recent samples (median of the last 10 gaps)."""
        times = [t for t, _ in list(self._samples)[-11:]]
        return float(np.median(np.diff(times))) if len(times) > 1 else default

    def delayed(self, now_ms: float, delay_ms: float) -> np.ndarray | None:
        return self.at(now_ms - delay_ms)

    def predicted(self, now_ms: float, delay_ms: float, dt_ms: float) -> np.ndarray | None:
        """The fix: guess ahead from old data only, like a headset does.

        guess = delayed position + velocity * delay, where velocity comes from
        the last two delayed positions (one frame interval dt_ms apart).
        """
        p0 = self.delayed(now_ms, delay_ms)
        if p0 is None or delay_ms <= 0:
            return p0
        p1 = self.delayed(now_ms, delay_ms + dt_ms)
        velocity = (p0 - p1) / dt_ms
        return p0 + velocity * delay_ms
