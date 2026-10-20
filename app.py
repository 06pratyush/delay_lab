"""Delay Lab: one window, one delay slider, switchable modes.

Keys:  A = AR-style   Q / Esc = quit
"""

from __future__ import annotations

import time
from collections import deque

import cv2
import numpy as np

from delay import MAX_DELAY_MS, DelayBuffer
from render import draw_sticker, draw_text_strip, draw_true_nose
from tracker import FaceTracker, open_camera, prepare

WINDOW = "Delay Lab"
SLIDER = "delay ms"
MODE_KEYS = {ord("a"): "AR"}
MODE_NAMES = {"AR": "AR-style"}
HINT = "A: AR   slider: delay   Q: quit"


class Smoother:
    """Rolling mean, so the on-screen numbers are readable from the back of the room."""

    def __init__(self, n: int = 15):
        self._vals: deque[float] = deque(maxlen=n)

    def add(self, v: float) -> float:
        if not np.isnan(v):
            self._vals.append(v)
        return float(np.mean(self._vals)) if self._vals else float("nan")


def main() -> None:
    cap = open_camera()
    cv2.namedWindow(WINDOW)
    cv2.createTrackbar(SLIDER, WINDOW, 0, MAX_DELAY_MS, lambda _v: None)

    buf = DelayBuffer()
    mode = "AR"
    face_w = 120.0
    fps_s, gap_s = Smoother(30), Smoother(15)
    t_prev = time.perf_counter()

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
            sticker = buf.delayed(now_ms, delay_ms)
            gap = float(np.linalg.norm(face.nose - sticker)) if face and sticker is not None else float("nan")
            gap_shown = gap_s.add(gap)

            view = frame
            if sticker is not None:
                if face:
                    draw_true_nose(view, face.nose)
                draw_sticker(view, sticker, face_w)

            status = f"{MODE_NAMES[mode]}  |  delay {delay_ms:3d} ms  |  "
            status += f"gap {gap_shown:5.1f} px" if face else "no face"
            status += f"  |  {fps:4.1f} fps"
            draw_text_strip(view, status, HINT)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in MODE_KEYS:
                mode = MODE_KEYS[key]

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
