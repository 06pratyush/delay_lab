"""Delay Lab: one window, one delay slider, switchable modes.

Keys:  V = VR-style   A = AR-style   F = AR + fix   R = record   S = sweep   Q / Esc = quit
"""

from __future__ import annotations

import csv
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import sweep
from delay import MAX_DELAY_MS, DelayBuffer
from paths import LOGS, RECORDINGS
from render import draw_room, draw_sticker, draw_text_strip, draw_true_nose, view_from_nose
from tracker import FaceTracker, open_camera, prepare

WINDOW = "Delay Lab"
SLIDER = "delay ms"
MODE_KEYS = {ord("v"): "VR", ord("a"): "AR", ord("f"): "FIX"}
MODE_NAMES = {"VR": "VR-style", "AR": "AR-style", "FIX": "AR + fix"}
HINT = "V: VR   A: AR   F: AR + fix   slider: delay   R: record   S: sweep   Q: quit"


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

    def __init__(self, folder: Path = LOGS):
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


class Recorder:
    """Saves raw camera frames to recordings/ for the sweep, plus each frame's real capture time."""

    def __init__(self, folder: Path = RECORDINGS):
        self.folder = folder
        self._writer = None
        self._times: list[float] = []
        self.path: Path | None = None

    @property
    def active(self) -> bool:
        return self._writer is not None

    def start(self, frame: np.ndarray, fps: float) -> None:
        self.folder.mkdir(exist_ok=True)
        self.path = self.folder / f"head_{stamp()}.mp4"
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(str(self.path), fourcc, max(round(fps), 1), (w, h))
        self._times = []

    def write(self, frame: np.ndarray, t_ms: float) -> None:
        self._writer.write(frame)
        self._times.append(t_ms)

    @property
    def seconds(self) -> float:
        return (self._times[-1] - self._times[0]) / 1000 if len(self._times) > 1 else 0.0

    def stop(self) -> Path:
        self._writer.release()
        self._writer = None
        t0 = self._times[0] if self._times else 0.0
        with open(self.path.with_suffix(".times.csv"), "w", newline="") as f:
            f.write("t_ms\n" + "".join(f"{t - t0:.3f}\n" for t in self._times))
        return self.path


def run_sweep_from_app(frame_shape) -> None:
    """S key: sweep the newest recording, showing progress, then the chart."""
    path = sweep.latest_recording()
    if path is None:
        print("No recording yet: press R, turn your head side to side for ~20 s, press R again.")
        return

    def progress(f: float) -> None:
        img = np.zeros(frame_shape, np.uint8)
        draw_text_strip(img, f"Sweeping {path.name}: tracking {f:4.0%}", "the app resumes when done")
        cv2.rectangle(img, (40, 220), (40 + int(560 * f), 260), (90, 220, 90), -1)
        cv2.rectangle(img, (40, 220), (600, 260), (255, 255, 255), 1)
        cv2.imshow(WINDOW, img)
        cv2.waitKey(1)

    try:
        df = sweep.sweep_video(path, progress=progress)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Sweep failed: {e}")
        return
    print(df.to_string(index=False))
    chart = cv2.imread(str(sweep.RESULTS / "sweep.png"))
    if chart is not None:
        cv2.imshow("Delay Lab - sweep chart", chart)
    print(f"Saved {sweep.RESULTS / 'sweep.csv'} and {sweep.RESULTS / 'sweep.png'}")


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
    rec = Recorder()
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

            if rec.active:
                rec.write(raw, now_ms)  # raw = un-mirrored; the sweep runs prepare() itself
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
            if rec.active:
                status += f"  |  REC {rec.seconds:4.1f} s"
            draw_text_strip(view, status, HINT)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord("r"):
                if rec.active:
                    print(f"Saved recording {rec.stop()}")
                else:
                    rec.start(raw, fps)
                    print(f"Recording to {rec.path} (press R to stop)")
            if key == ord("s"):
                if rec.active:
                    print(f"Saved recording {rec.stop()}")
                run_sweep_from_app(frame.shape)
                t_prev = time.perf_counter()  # don't count the sweep as one long frame
            if key in MODE_KEYS:
                mode = MODE_KEYS[key]

    if rec.active:
        print(f"Saved recording {rec.stop()}")
    log.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
