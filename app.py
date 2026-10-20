"""Delay Lab: one window, one delay slider, switchable modes.

Keys:  V = VR-style   A = AR-style   F = AR + fix   Q / Esc = quit
"""

from __future__ import annotations

import csv
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from delay import MAX_DELAY_MS, DelayBuffer
from render import draw_room, draw_sticker, draw_text_strip, draw_true_nose, view_from_nose
from tracker import FaceTracker, open_camera, prepare

ROOT = Path(__file__).parent
WINDOW = "Delay Lab"
SLIDER = "delay ms"
MODE_KEYS = {ord("v"): "VR", ord("a"): "AR", ord("f"): "FIX"}
MODE_NAMES = {"VR": "VR-style", "AR": "AR-style", "FIX": "AR + fix"}
HINT = "V: VR   A: AR   F: AR + fix   slider: delay   Q: quit"


class Smoother:
    """Rolling mean, so the on-screen numbers are readable from the back of the room."""

    def __init__(self, n: int = 15):
        self._vals: deque[float] = deque(maxlen=n)

    def add(self, v: float) -> float:
        if not np.isnan(v):
            self._vals.append(v)
        return float(np.mean(self._vals)) if self._vals else float("nan")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class SessionLog:
    """One CSV row per frame, in every mode (VR gaps are logged but never shown)."""

    COLUMNS = ["t_ms", "mode", "delay_ms", "nose_x", "nose_y", "sticker_x", "sticker_y",
               "gap_px", "face_w_px", "fps"]

    def __init__(self, folder: Path = ROOT / "logs"):
        folder.mkdir(exist_ok=True)
        self.path = folder / f"session_{stamp()}.csv"
        self._file = open(self.path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.COLUMNS)

    def row(self, t_ms, mode, delay_ms, nose, sticker, gap, face_w, fps) -> None:
        nx, ny = nose if nose is not None else ("", "")
        sx, sy = sticker if sticker is not None else ("", "")
        vals = [t_ms, mode, delay_ms, nx, ny, sx, sy, gap, face_w, fps]
        self._writer.writerow([f"{v:.2f}" if isinstance(v, float) else v for v in vals])

    def close(self) -> None:
        self._file.close()


def main() -> None:
    cap = open_camera()
    cv2.namedWindow(WINDOW)
    cv2.createTrackbar(SLIDER, WINDOW, 0, MAX_DELAY_MS, lambda _v: None)

    buf = DelayBuffer()
    mode = "AR"
    face_w = 120.0
    fps_s, gap_s = Smoother(30), Smoother(15)
    t_prev = time.perf_counter()
    log = SessionLog()
    print(f"Logging to {log.path}")

    with FaceTracker() as tracker:
        while True:
            ok, raw = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break
            t_now = time.perf_counter()
            now_ms = t_now * 1000
            fps = fps_s.add(1 / max(t_now - t_prev, 1e-6))
            t_prev = t_now

            frame = prepare(raw)
            face = tracker.detect(frame, now_ms)
            if face:
                buf.push(now_ms, face.nose)
                face_w = face.width

            delay_ms = cv2.getTrackbarPos(SLIDER, WINDOW)
            if mode == "FIX":
                sticker = buf.predicted(now_ms, delay_ms, dt_ms=1000 / fps)
            else:
                sticker = buf.delayed(now_ms, delay_ms)
            gap = float(np.linalg.norm(face.nose - sticker)) if face and sticker is not None else float("nan")
            gap_shown = gap_s.add(gap)
            log.row(now_ms, mode, delay_ms, face.nose if face else None, sticker, gap, face_w, fps)

            if mode == "VR":
                # Camera picture hidden: the delayed nose only moves the viewpoint.
                view = np.zeros_like(frame)
                size = (frame.shape[1], frame.shape[0])
                draw_room(view, view_from_nose(sticker, size) if sticker is not None else (0.0, 0.0))
            else:
                view = frame
                if sticker is not None:
                    if face:
                        draw_true_nose(view, face.nose)
                    draw_sticker(view, sticker, face_w)

            status = f"{MODE_NAMES[mode]}  |  delay {delay_ms:3d} ms  |  "
            if not face:
                status += "no face"
            elif mode == "VR":
                status += "nothing real to compare"  # gap still logged, never shown
            else:
                status += f"gap {gap_shown:5.1f} px"
            status += f"  |  {fps:4.1f} fps"
            draw_text_strip(view, status, HINT)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in MODE_KEYS:
                mode = MODE_KEYS[key]

    log.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
