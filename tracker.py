"""MediaPipe Face Landmarker wrapper: frame -> nose tip and face width.

Run directly for a preview that draws a dot on your nose:
    python tracker.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

from paths import MODEL_PATH

NOSE_TIP = 1
LEFT_CHEEK, RIGHT_CHEEK = 234, 454  # outermost face-oval points, used for face width


@dataclass
class Face:
    nose: np.ndarray  # (x, y) in pixels
    width: float  # cheek-to-cheek distance in pixels; grows as you lean in


class FaceTracker:
    """Tracks one face in VIDEO mode. Timestamps must strictly increase."""

    def __init__(self, model_path=MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"{model_path} not found - run: python download_model.py")
        options = vision.FaceLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._last_ts = -1

    def detect(self, frame_bgr: np.ndarray, t_ms: float) -> Face | None:
        ts = max(int(t_ms), self._last_ts + 1)  # MediaPipe rejects repeated timestamps
        self._last_ts = ts
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
        if not result.face_landmarks:
            return None
        pts = result.face_landmarks[0]
        h, w = frame_bgr.shape[:2]

        def px(i: int) -> np.ndarray:
            return np.array([pts[i].x * w, pts[i].y * h])

        return Face(nose=px(NOSE_TIP), width=float(np.linalg.norm(px(RIGHT_CHEEK) - px(LEFT_CHEEK))))

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def open_camera(index: int = 0) -> cv2.VideoCapture:
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


def prepare(frame: np.ndarray) -> np.ndarray:
    """Mirror, then shrink to 640x480, so tracking and drawing share one image."""
    frame = cv2.flip(frame, 1)
    if frame.shape[1] != 640:
        frame = cv2.resize(frame, (640, 480))
    return frame


if __name__ == "__main__":
    cap = open_camera()
    with FaceTracker() as tracker:
        t_prev = time.perf_counter()
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = prepare(frame)
            now = time.perf_counter()
            face = tracker.detect(frame, now * 1000)
            fps, t_prev = 1 / max(now - t_prev, 1e-6), now
            if face:
                cv2.circle(frame, tuple(face.nose.astype(int)), 6, (0, 0, 255), -1)
            cv2.putText(frame, f"{fps:4.1f} fps  {'face' if face else 'no face'}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Delay Lab - tracker preview (q to quit)", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    cap.release()
    cv2.destroyAllWindows()
