"""Turn a demo recording (what the window showed) into a small GIF for the README.

    python make_gif.py                               # newest recordings/demo_*.mp4
    python make_gif.py recordings/demo_x.mp4 --start 3 --seconds 6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
from PIL import Image

from paths import RECORDINGS, RESULTS


def latest_demo() -> Path | None:
    videos = sorted(RECORDINGS.glob("demo_*.mp4"), key=lambda p: p.stat().st_mtime)
    return videos[-1] if videos else None


def make_gif(video: Path, out: Path, start: float = 0.0, seconds: float = 6.0,
             width: int = 480, fps: float = 12.0) -> int:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(src_fps / fps, 1.0)  # keep every step-th frame
    first, last = int(start * src_fps), int((start + seconds) * src_fps)
    frames, i, next_keep = [], 0, float(first)
    while i < last:
        ok, frame = cap.read()
        if not ok:
            break
        if i >= next_keep:
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (width, round(h * width / w)), interpolation=cv2.INTER_AREA)
            frames.append(Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB)))
            next_keep += step
        i += 1
    cap.release()
    if not frames:
        raise RuntimeError(f"No frames between {start} s and {start + seconds} s in {video.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0,
                   duration=round(1000 * step / src_fps), optimize=True)
    return len(frames)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", nargs="?", type=Path, help="default: newest recordings/demo_*.mp4")
    ap.add_argument("--out", type=Path, default=RESULTS / "demo.gif")
    ap.add_argument("--start", type=float, default=0.0, help="seconds into the video")
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--fps", type=float, default=12.0)
    args = ap.parse_args()
    video = args.video or latest_demo()
    if video is None:
        print("No demo video yet: in the app press R, show the effect, press R again.")
        return 1
    try:
        n = make_gif(video, args.out, args.start, args.seconds, args.width, args.fps)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"GIF failed: {e}")
        return 1
    print(f"Saved {args.out} ({n} frames, {args.out.stat().st_size / 1e6:.1f} MB) from {video.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
