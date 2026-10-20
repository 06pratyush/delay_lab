"""Delay Lab: one window, one delay slider, switchable modes.

Keys:  V = VR-style   A = AR-style   F = AR + fix   R = record   S = sweep
       W = fullscreen   Q / Esc = quit

    python app.py                 # normal use
    python app.py --camera 1      # pick another webcam
    python app.py --selftest 8    # drive every mode by itself for 8 s, then quit
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import sweep
from delay import MAX_DELAY_MS, DelayBuffer
from paths import LOGS, RECORDINGS, RESULTS
from render import draw_room, draw_sticker, draw_text_strip, draw_true_nose, view_from_nose
from tracker import FaceTracker, open_camera, prepare

WINDOW = "Delay Lab"
SLIDER = "delay ms"
MODE_KEYS = {ord("v"): "VR", ord("a"): "AR", ord("f"): "FIX"}
MODE_NAMES = {"VR": "VR-style", "AR": "AR-style", "FIX": "AR + fix"}
HINT = "V: VR   A: AR   F: AR + fix   slider: delay   R: record   S: sweep   W: fullscreen   Q: quit"


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
        folder.mkdir(parents=True, exist_ok=True)
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
    """R key. Saves two videos side by side:

    head_<stamp>.mp4  raw camera frames (+ .times.csv of real capture times) for the sweep
    demo_<stamp>.mp4  exactly what the window shows, for the README GIF and slides
    """

    def __init__(self, folder: Path = RECORDINGS):
        self.folder = folder
        self._raw = self._view = None
        self._times: list[float] = []
        self.path: Path | None = None

    @property
    def active(self) -> bool:
        return self._raw is not None

    def start(self, raw: np.ndarray, view: np.ndarray, fps: float) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        s = stamp()
        self.path = self.folder / f"head_{s}.mp4"
        self.demo_path = self.folder / f"demo_{s}.mp4"
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        rate = max(round(fps), 1)
        self._raw = cv2.VideoWriter(str(self.path), fourcc, rate, (raw.shape[1], raw.shape[0]))
        self._view = cv2.VideoWriter(str(self.demo_path), fourcc, rate, (view.shape[1], view.shape[0]))
        self._times = []

    def write(self, raw: np.ndarray, view: np.ndarray, t_ms: float) -> None:
        self._raw.write(raw)
        self._view.write(view)
        self._times.append(t_ms)

    @property
    def seconds(self) -> float:
        return (self._times[-1] - self._times[0]) / 1000 if len(self._times) > 1 else 0.0

    def stop(self) -> Path:
        self._raw.release()
        self._view.release()
        self._raw = self._view = None
        t0 = self._times[0] if self._times else 0.0
        with open(self.path.with_suffix(".times.csv"), "w", newline="") as f:
            f.write("t_ms\n" + "".join(f"{t - t0:.3f}\n" for t in self._times))
        print(f"Saved {self.path.name} (for the sweep) and {self.demo_path.name} (demo) in {self.folder}")
        return self.path


class SelfTest:
    """Presses the keys and moves the slider on a timetable, so the app can check itself."""

    def __init__(self, seconds: float):
        self.t0 = time.perf_counter()
        self.seconds = seconds
        plan = [(0.00, "a", 0), (0.15, None, 100), (0.30, "f", None), (0.45, "v", None),
                (0.55, "r", None), (0.80, "r", None), (0.85, "s", None), (1.00, "q", None)]
        self._steps = deque((f * seconds, k, d) for f, k, d in plan)

    def next_key(self) -> int:
        """Returns the scripted key press due now (or -1), applying slider moves itself."""
        elapsed = time.perf_counter() - self.t0
        if self._steps and self._steps[0][0] <= elapsed:
            _, key, delay = self._steps.popleft()
            if delay is not None:
                cv2.setTrackbarPos(SLIDER, WINDOW, delay)
            return ord(key) if key else -1
        return -1


def run_sweep_from_app(frame_shape, path: Path | None = None, out_dir: Path = RESULTS) -> bool:
    """S key: sweep a recording (default: the newest), showing progress, then the chart."""
    path = path or sweep.latest_recording()
    if path is None:
        print("No recording yet: press R, turn your head side to side for ~20 s, press R again.")
        return False

    def progress(f: float) -> None:
        img = np.zeros(frame_shape, np.uint8)
        draw_text_strip(img, f"Sweeping {path.name}: tracking {f:4.0%}", "the app resumes when done")
        cv2.rectangle(img, (40, 220), (40 + int(560 * f), 260), (90, 220, 90), -1)
        cv2.rectangle(img, (40, 220), (600, 260), (255, 255, 255), 1)
        cv2.imshow(WINDOW, img)
        cv2.waitKey(1)

    try:
        df = sweep.sweep_video(path, out_dir, progress=progress)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Sweep failed: {e}")
        return False
    print(df.to_string(index=False))
    chart = cv2.imread(str(out_dir / "sweep.png"))
    if chart is not None:
        cv2.imshow("Delay Lab - sweep chart", chart)
    print(f"Saved {out_dir / 'sweep.csv'} and {out_dir / 'sweep.png'}")
    return True


def toggle_fullscreen() -> None:
    full = cv2.getWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN) == cv2.WINDOW_FULLSCREEN
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL if full else cv2.WINDOW_FULLSCREEN)


def draw_rec_badge(img: np.ndarray, seconds: float) -> None:
    """Drawn after the frame is recorded, so the demo video itself stays clean."""
    h = img.shape[0]
    cv2.circle(img, (20, h - 20), 8, (0, 0, 255), -1, cv2.LINE_AA)
    cv2.putText(img, f"REC {seconds:4.1f} s", (36, h - 13), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2, cv2.LINE_AA)


def main(camera: int = 0, selftest: float | None = None) -> int:
    cap = open_camera(camera)
    ok, raw = cap.read()
    if not ok:
        print(f"Could not read from camera {camera}. Is another app using it? Try --camera 1.")
        return 1

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # drag to resize for a projector
    cv2.createTrackbar(SLIDER, WINDOW, 0, MAX_DELAY_MS, lambda _v: None)

    script = SelfTest(selftest) if selftest else None
    rec_folder = RECORDINGS / "selftest" if script else RECORDINGS
    results = RESULTS / "selftest" if script else RESULTS
    buf = DelayBuffer()
    mode = "AR"
    face_w = 120.0
    fps_s, gap_s = Smoother(30), Smoother(15)
    stats: dict[str, list[float]] = defaultdict(list)
    frames = faces = 0
    intervals: list[float] = []
    swept = None
    t_prev = time.perf_counter()
    log = SessionLog()
    rec = Recorder(rec_folder)
    print(f"Logging to {log.path}")

    with FaceTracker() as tracker:
        while True:
            if frames:  # the first frame was already read above
                ok, raw = cap.read()
                if not ok:
                    print("Camera stopped delivering frames.")
                    break
            t_now = time.perf_counter()
            now_ms = t_now * 1000
            if script:
                intervals.append(t_now - t_prev)
            fps = fps_s.add(1 / max(t_now - t_prev, 1e-6))
            t_prev = t_now
            frames += 1

            frame = prepare(raw)
            face = tracker.detect(frame, now_ms)
            if face:
                faces += 1
                buf.push(now_ms, face.nose)
                face_w = face.width

            delay_ms = cv2.getTrackbarPos(SLIDER, WINDOW)
            if mode == "FIX":
                sticker = buf.predicted(now_ms, delay_ms, dt_ms=buf.frame_interval_ms())
            else:
                sticker = buf.delayed(now_ms, delay_ms)
            gap = float(np.linalg.norm(face.nose - sticker)) if face and sticker is not None else float("nan")
            gap_shown = gap_s.add(gap)
            log.row(now_ms, mode, delay_ms, face.nose if face else None, sticker, gap, face_w, fps)
            if not np.isnan(gap):
                stats[f"{MODE_NAMES[mode]} @ {delay_ms} ms"].append(gap)

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
            if rec.active:
                rec.write(raw, view, now_ms)  # raw = un-mirrored; the sweep runs prepare() itself
                draw_rec_badge(view, rec.seconds)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if script:
                key = script.next_key() & 0xFF if key == 255 else key
            if key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord("r"):
                if rec.active:
                    rec.stop()
                else:
                    rec.start(raw, view, fps)
                    print(f"Recording to {rec.path} (press R to stop)")
            if key == ord("s"):
                if rec.active:
                    rec.stop()
                swept = run_sweep_from_app(frame.shape, rec.path if script else None, results)
                # The camera kept buffering during the sweep: start the clocks afresh.
                buf.clear()
                fps_s = Smoother(30)
                t_prev = time.perf_counter()
            if key == ord("w"):
                toggle_fullscreen()
            if key in MODE_KEYS:
                mode = MODE_KEYS[key]

    if rec.active:
        rec.stop()
    log.close()
    cap.release()
    cv2.destroyAllWindows()

    if script:
        print(f"\nSelf-test: {frames} frames, face in {faces} ({faces / frames:.0%}), "
              f"median {1 / np.median(intervals[1:] or [1]):.1f} fps, sweep {'OK' if swept else 'not run' if swept is None else 'FAILED'}")
        for name, gaps in stats.items():
            print(f"  {name:22s} mean gap {np.mean(gaps):6.1f} px  ({len(gaps)} frames)")
        return 0 if frames > 0 else 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Delay Lab: see why AR punishes delay more than VR.")
    ap.add_argument("--camera", type=int, default=0, help="webcam index (default 0)")
    ap.add_argument("--selftest", type=float, metavar="SECONDS",
                    help="cycle through every mode automatically, record, sweep, then quit")
    args = ap.parse_args()
    sys.exit(main(args.camera, args.selftest))
