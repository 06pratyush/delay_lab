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
              f"calculated, not measured: head turning at {HEAD_SPEED_DEG_S}°/s, slip = speed × delay")


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


# --- Simulated demo ------------------------------------------------------------
# A cartoon head swings side to side; Delay Lab's own DelayBuffer, prediction and
# drawing code produce each panel. No camera is involved, and every frame says so.

PANEL = (400, 300)  # width, height of each of the three panels
DEMO_DELAY_MS = 100
DEMO_FPS = 15
SKIN, SKIN_EDGE, HAIR, BACKDROP = (165, 201, 241), (115, 154, 201), (32, 42, 59), (239, 231, 223)


def _head_x(t_s: float) -> float:
    return PANEL[0] / 2 + 85 * np.sin(2 * np.pi * t_s / 2.0)  # one full swing every 2 s


def _draw_head(img: np.ndarray, cx: float) -> np.ndarray:
    """Cartoon head; returns the nose tip position (what the tracker would report)."""
    cx, cy = int(round(cx)), 165
    cv2.ellipse(img, (cx, cy + 118), (95, 45), 0, 180, 360, (163, 140, 122), -1, cv2.LINE_AA)  # shoulders
    cv2.rectangle(img, (cx - 14, cy + 40), (cx + 14, cy + 78), (148, 185, 230), -1)              # neck
    cv2.ellipse(img, (cx, cy), (48, 60), 0, 0, 360, SKIN, -1, cv2.LINE_AA)
    cv2.ellipse(img, (cx, cy), (48, 60), 0, 0, 360, SKIN_EDGE, 2, cv2.LINE_AA)
    cv2.ellipse(img, (cx, cy - 22), (50, 40), 0, 180, 360, HAIR, -1, cv2.LINE_AA)
    for dx in (-17, 17):
        cv2.ellipse(img, (cx + dx, cy - 2), (4, 5), 0, 0, 360, (43, 43, 43), -1, cv2.LINE_AA)
    cv2.ellipse(img, (cx, cy + 32), (13, 6), 0, 0, 180, (74, 90, 160), 2, cv2.LINE_AA)
    return np.array([cx, cy + 14], dtype=float)


def _demo_frames(seconds: float = 4.0):
    from delay import DelayBuffer

    buf = DelayBuffer()
    dt_ms = 1000 / DEMO_FPS
    w, h = PANEL
    gaps = {"AR": [], "FIX": []}
    for i in range(int(-1.0 * DEMO_FPS), int(seconds * DEMO_FPS)):  # 1 s warm-up fills the buffer
        t_ms = i * dt_ms
        ar = np.full((h, w, 3), BACKDROP, np.uint8)
        nose = _draw_head(ar, _head_x(t_ms / 1000))
        buf.push(t_ms, nose)
        fix = ar.copy()
        late = buf.delayed(t_ms, DEMO_DELAY_MS)
        guess = buf.predicted(t_ms, DEMO_DELAY_MS, dt_ms)
        vr = np.zeros((h, w, 3), np.uint8)
        render.draw_room(vr, render.view_from_nose(late, (w, h)))
        for img, drawn, key in ((ar, late, "AR"), (fix, guess, "FIX")):
            render.draw_true_nose(img, nose)
            render.draw_sticker(img, drawn, 110)
            gaps[key].append(float(np.linalg.norm(nose - drawn)))
            gaps[key] = gaps[key][-8:]  # short rolling mean, like the app's strip
        if i < 0:
            continue
        render.draw_text_strip(vr, f"VR-style | {DEMO_DELAY_MS} ms | nothing to compare")
        render.draw_text_strip(ar, f"AR-style | {DEMO_DELAY_MS} ms | gap {np.mean(gaps['AR']):4.0f} px")
        render.draw_text_strip(fix, f"AR + fix | {DEMO_DELAY_MS} ms | gap {np.mean(gaps['FIX']):4.0f} px")
        row = np.hstack([vr, np.full((h, 4, 3), 255, np.uint8), ar, np.full((h, 4, 3), 255, np.uint8), fix])
        footer = np.full((26, row.shape[1], 3), (40, 40, 40), np.uint8)
        cv2.putText(footer, "SIMULATED: synthetic head, real Delay Lab delay + drawing code. Not a webcam recording.",
                    (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
        yield np.vstack([row, footer])


def demo_gif(out: Path) -> None:
    from PIL import Image

    frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in _demo_frames()]
    # One shared palette from a strip of sample frames, so small marks (the green cross) keep their colour.
    sample = Image.new("RGB", (frames[0].width, frames[0].height * 4))
    for k, f in enumerate(frames[:: max(len(frames) // 4, 1)][:4]):
        sample.paste(f, (0, k * frames[0].height))
    palette = sample.quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0,
                   duration=round(1000 / DEMO_FPS), optimize=True)


def social_preview(out: Path) -> None:
    """1280x640 card for link previews (upload in Settings -> General -> Social preview)."""
    from PIL import Image, ImageDraw, ImageFont

    def font(bold: bool, size: int):
        name = "segoeuib.ttf" if bold else "segoeui.ttf"
        for path in (Path("C:/Windows/Fonts") / name, Path(name)):
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
        return ImageFont.load_default()

    card = Image.new("RGB", (1280, 640), cs.SURFACE)
    d = ImageDraw.Draw(card)
    d.text((72, 70), "Delay Lab", font=font(True, 88), fill=cs.INK)
    sub, words, line = font(False, 36), "Why AR punishes headset delay more than VR, shown on a laptop webcam.".split(), ""
    lines = []
    for word in words:  # wrap to the left column (the picture starts at x=660)
        if d.textlength(f"{line} {word}".strip(), font=sub) > 540:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    for i, text in enumerate(lines + [line]):
        d.text((76, 178 + i * 46), text, font=sub, fill=cs.INK_2)
    d.rounded_rectangle((72, 340, 610, 414), radius=14, fill="#eef4fc")
    d.text((96, 354), "slip = head speed × delay", font=font(True, 34), fill=cs.SERIES[0])
    for i, line in enumerate(["V  VR-style: the whole world is late", "A  AR-style: the sticker slides off",
                              "F  AR + fix: guess where the head goes"]):
        d.text((76, 452 + i * 46), line, font=font(False, 28), fill=cs.INK)
    frames = list(_demo_frames(1.0))
    # Frame 0: head centred and moving fastest, so the late sticker trails furthest.
    ar = cv2.cvtColor(frames[0][:PANEL[1], PANEL[0] + 4:2 * PANEL[0] + 4], cv2.COLOR_BGR2RGB)
    panel = Image.fromarray(ar).resize((560, 420))
    card.paste(panel, (660, 96))
    d.text((660, 526), "simulated frame, 100 ms delay", font=font(False, 22), fill=cs.MUTED)
    d.text((660, 570), "github.com/06pratyush/delay_lab", font=font(True, 26), fill=cs.INK_2)
    card.save(out, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    slip_chart(OUT / "slip_vs_delay.png")
    expected_sweep(OUT / "expected_sweep.png")
    vr_screenshot(OUT / "vr_room.png")
    demo_gif(OUT / "demo_simulated.gif")
    social_preview(OUT / "social_preview.png")
    print(f"Wrote figures to {OUT}")
