"""The sweep: one recorded video -> every delay, with and without the fix -> CSV + chart.

    python sweep.py                      # newest video in recordings/
    python sweep.py path/to/video.mp4

The video is tracked once; each of the 12 runs then replays the same nose track
through the same DelayBuffer the live app uses, so the chart is identical every run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import pandas as pd

from delay import MAX_DELAY_MS, DelayBuffer
from paths import RECORDINGS, RESULTS

DELAYS_MS = [0, 25, 50, 75, 100, 150]


def latest_recording() -> Path | None:
    # head_*.mp4 only: demo_*.mp4 files have the sticker and text drawn on them.
    videos = sorted(RECORDINGS.glob("head_*.mp4"), key=lambda p: p.stat().st_mtime)
    return videos[-1] if videos else None


def track_video(path: Path, progress: Callable[[float], None] | None = None):
    """Returns (t_ms, nose) arrays; nose rows are NaN where no face was found."""
    from tracker import FaceTracker, prepare  # MediaPipe only needed here, not for replay

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    # Prefer the real capture times saved by the app; fall back to frame / fps.
    sidecar = path.with_suffix(".times.csv")
    real_times = pd.read_csv(sidecar).t_ms.to_numpy() if sidecar.exists() else None
    times, noses = [], []
    with FaceTracker() as tracker:
        i = 0
        while True:
            ok, raw = cap.read()
            if not ok:
                break
            # Recorded time, not wall-clock: makes runs repeatable.
            t_ms = real_times[i] if real_times is not None and i < len(real_times) else i * 1000.0 / fps
            face = tracker.detect(prepare(raw), t_ms)
            times.append(t_ms)
            noses.append(face.nose if face else (np.nan, np.nan))
            i += 1
            if progress and i % 10 == 0:
                progress(min(i / total, 1.0))
    cap.release()
    return np.array(times), np.array(noses, dtype=float)


def replay(t_ms: np.ndarray, nose: np.ndarray, delay_ms: float, fix: bool) -> np.ndarray:
    """Per-frame gap (px) between the true nose and the drawn sticker."""
    dt = float(np.median(np.diff(t_ms)))
    # Skip the same warm-up at every delay, so all runs average over the same frames.
    start = t_ms[0] + MAX_DELAY_MS + 2 * dt
    buf = DelayBuffer()
    gaps = []
    for t, p in zip(t_ms, nose):
        if np.isnan(p[0]):
            continue
        buf.push(t, p)
        if t < start:
            continue
        drawn = buf.predicted(t, delay_ms, dt) if fix else buf.delayed(t, delay_ms)
        gaps.append(np.linalg.norm(p - drawn))
    return np.array(gaps)


def run_sweep(t_ms: np.ndarray, nose: np.ndarray, delays=DELAYS_MS) -> pd.DataFrame:
    rows = []
    for fix in (False, True):
        for d in delays:
            g = replay(t_ms, nose, d, fix)
            rows.append({
                "delay_ms": d,
                "fix": fix,
                "mean_gap_px": round(float(g.mean()), 3),
                "median_gap_px": round(float(np.median(g)), 3),
                "p95_gap_px": round(float(np.percentile(g, 95)), 3),
                "frames": len(g),
            })
    return pd.DataFrame(rows)


def mean_speed_px_per_ms(t_ms: np.ndarray, nose: np.ndarray) -> float:
    ok = ~np.isnan(nose[:, 0])
    t, p = t_ms[ok], nose[ok]
    return float(np.mean(np.linalg.norm(np.diff(p, axis=0), axis=1) / np.diff(t)))


# Savitzky-Golay (7 points, quadratic): follows smooth head motion exactly, ignores jitter.
_SG7 = np.array([-2, 3, 6, 7, 6, 3, -2]) / 21


def noise_floor_px(nose: np.ndarray) -> float:
    """Tracker jitter: mean distance between each nose dot and a smooth local fit.

    The gap at 0 ms is zero by construction (sticker and truth are the same dot),
    so this is the honest floor: wobble that is there even with no delay at all.
    Only runs of 7 consecutive frames with a face are used.
    """
    ok = ~np.isnan(nose[:, 0])
    full = np.convolve(ok.astype(int), np.ones(7, int), mode="valid") == 7
    if not full.any():
        return float("nan")
    filled = np.where(ok[:, None], nose, 0.0)
    smooth = np.column_stack([np.convolve(filled[:, i], _SG7[::-1], mode="valid") for i in (0, 1)])
    centre = nose[3:-3]
    return float(np.mean(np.linalg.norm(centre[full] - smooth[full], axis=1)))


def plot(df: pd.DataFrame, out: Path, speed: float | None = None, title: str = "",
         noise: float | None = None,
         subtitle: str = "same recorded head motion replayed at every delay") -> None:
    import chart_style as cs

    fig, ax = cs.new_figure()
    off, on = df[~df.fix], df[df.fix]
    if noise and not np.isnan(noise):
        ax.axhspan(0, noise, color=cs.MUTED, alpha=0.18, lw=0,
                   label=f"tracker jitter ≈ {noise:.1f} px (noise floor)")
    if speed:
        d = np.array([0, max(df.delay_ms)])
        ax.plot(d, speed * d, ":", color=cs.MUTED, lw=1.2, label="prediction: slip = head speed × delay")
    for part, color, name in ((off, cs.SERIES[0], "without fix"), (on, cs.SERIES[1], "with fix")):
        ax.plot(part.delay_ms, part.mean_gap_px, "-o", color=color, lw=1.6, ms=5,
                mec=cs.SURFACE, mew=1.2, label=name, zorder=3)
        x, y = part.delay_ms.iloc[-1], part.mean_gap_px.iloc[-1]
        ax.annotate(f"{name}\n{y:.1f} px", (x, y), xytext=(8, 0), textcoords="offset points",
                    va="center", color=cs.INK_2, fontsize=9)
    ax.set_xlabel("added delay (ms)", color=cs.INK_2)
    ax.set_ylabel("average sticker gap (pixels)", color=cs.INK_2)
    ax.set_xlim(0, max(df.delay_ms) * 1.18)  # room for the end labels
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left", labelcolor=cs.INK_2, fontsize=9)
    cs.finish(fig, ax, out, title or "AR sticker error vs added delay", subtitle)


def sweep_video(path: Path, out_dir: Path = RESULTS, progress=None) -> pd.DataFrame:
    t_ms, nose = track_video(path, progress)
    found = int((~np.isnan(nose[:, 0])).sum())
    if found < 10:
        raise RuntimeError(f"Face found in only {found} of {len(t_ms)} frames of {path.name}")
    df = run_sweep(t_ms, nose)
    noise = noise_floor_px(nose)
    df["noise_floor_px"] = round(noise, 3)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sweep.csv", index=False)
    pd.DataFrame({"t_ms": t_ms, "nose_x": nose[:, 0], "nose_y": nose[:, 1]}).to_csv(
        out_dir / "track.csv", index=False)
    plot(df, out_dir / "sweep.png", mean_speed_px_per_ms(t_ms, nose), f"Delay Lab sweep: {path.name}", noise)
    return df


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else latest_recording()
    if path is None:
        print("No video given and no head_*.mp4 in recordings/. Record one in the app with R.")
        return 1
    print(f"Sweeping {path}")
    try:
        df = sweep_video(path, progress=lambda f: print(f"\r  tracking {f:4.0%}", end="", flush=True))
    except (RuntimeError, FileNotFoundError) as e:
        print(f"\nSweep failed: {e}")
        return 1
    print()
    print(df.to_string(index=False))
    print(f"Saved {RESULTS / 'sweep.csv'} and {RESULTS / 'sweep.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
