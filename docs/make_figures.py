"""Regenerate the README figures in docs/img/ (no webcam needed).

    python docs/make_figures.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import chart_style as cs  # noqa: E402
import render  # noqa: E402
import sweep  # noqa: E402

OUT = ROOT / "docs" / "img"
HEAD_SPEED_DEG_S = 100  # a normal, unhurried head turn


def slip_cm(delay_ms):
    """How far an AR object 1 m away slips: angle = speed x delay, arc = angle x 1 m."""
    return np.radians(HEAD_SPEED_DEG_S * np.asarray(delay_ms) / 1000) * 100


def slip_chart(out: Path) -> None:
    fig, ax = cs.new_figure(7.4, 4.0)
    d = np.linspace(0, 150, 151)
    ax.axvspan(0, 20, color=cs.SERIES[0], alpha=0.07, lw=0)
    ax.text(10, slip_cm(150) * 0.97, "comfort\ntarget\n< 20 ms", ha="center", va="top",
            color=cs.INK_2, fontsize=8)
    ax.axvline(50, color=cs.MUTED, lw=1, ls="--")
    ax.text(51.5, slip_cm(150) * 0.97, "≈ 50 ms: many people\nfeel sick in VR", va="top",
            color=cs.INK_2, fontsize=8)
    ax.plot(d, slip_cm(d), color=cs.SERIES[0], lw=1.8, zorder=2)
    systems = [  # (name, low ms, high ms, label position in data units)
        ("Apple Vision Pro", 11, 11, (14, 11.5)),
        ("Meta Quest 3", 35, 40, (54, 4.6)),
        ("laptop webcam\n(Delay Lab's baseline)", 60, 150, (108, 13.5)),
    ]
    for name, lo, hi, at in systems:
        mid = (lo + hi) / 2
        if hi > lo:
            ax.plot([lo, hi], slip_cm([lo, hi]), color=cs.INK, lw=4, alpha=0.25,
                    solid_capstyle="round", zorder=3)
        ax.plot(mid, slip_cm(mid), "o", ms=7, color=cs.INK, mec=cs.SURFACE, mew=1.5, zorder=4)
        span = f"{lo}" if lo == hi else f"{lo}–{hi}"
        ax.annotate(f"{name}\n{span} ms → {slip_cm(lo):.1f}" + ("" if lo == hi else f"–{slip_cm(hi):.0f}") + " cm",
                    (mid, slip_cm(mid)), xytext=at, textcoords="data", color=cs.INK_2, fontsize=8.5,
                    va="top", arrowprops={"arrowstyle": "-", "color": cs.MUTED, "lw": 0.8,
                                          "shrinkA": 2, "shrinkB": 5})
    ax.set_xlim(0, 155)
    ax.set_ylim(0, slip_cm(150) * 1.02)
    ax.set_xlabel("motion-to-photon delay (ms)", color=cs.INK_2)
    ax.set_ylabel("AR object slip at 1 m (cm)", color=cs.INK_2)
    cs.finish(fig, ax, out, "How far an AR object slips during a normal head turn",
              f"head turning at {HEAD_SPEED_DEG_S}°/s; slip = speed × delay")


def expected_sweep(out: Path) -> None:
    t = np.arange(0, 20_000, 1000 / 30)
    rng = np.random.default_rng(1)
    x = 320 + 150 * np.sin(2 * np.pi * t / 2000) + rng.normal(0, 0.3, t.size)
    nose = np.column_stack([x, 240 + rng.normal(0, 0.3, t.size)])
    sweep.plot(sweep.run_sweep(t, nose), out, sweep.mean_speed_px_per_ms(t, nose),
               "Expected result (synthetic, not a real recording)", sweep.noise_floor_px(nose),
               "smooth sine-wave head motion, 20 s at 30 fps, replayed at every delay")


def vr_screenshot(out: Path) -> None:
    img = np.zeros((480, 640, 3), np.uint8)
    render.draw_room(img, render.view_from_nose((230, 220), (640, 480)))  # head leaning left
    render.draw_text_strip(img, "VR-style  |  delay 100 ms  |  nothing real to compare  |  30.1 fps",
                           "V: VR   A: AR   F: AR + fix   slider: delay   R: record   S: sweep")
    cv2.imwrite(str(out), img)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    slip_chart(OUT / "slip_vs_delay.png")
    expected_sweep(OUT / "expected_sweep.png")
    vr_screenshot(OUT / "vr_room.png")
    print(f"Wrote figures to {OUT}")
