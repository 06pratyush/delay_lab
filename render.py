"""Drawing: the AR sticker and the text strip."""

from __future__ import annotations

import cv2
import numpy as np

RED = (40, 40, 230)
WHITE = (255, 255, 255)
GREEN = (90, 220, 90)


def draw_sticker(img: np.ndarray, xy, face_width: float) -> None:
    """A red disc with a white ring, sized to the face so it reads as 'stuck on'."""
    r = max(6, int(face_width * 0.06))
    c = tuple(int(v) for v in xy)
    cv2.circle(img, c, r, RED, -1, cv2.LINE_AA)
    cv2.circle(img, c, r, WHITE, 2, cv2.LINE_AA)


def draw_true_nose(img: np.ndarray, xy) -> None:
    """Small green cross on the real (current) nose, so the gap is visible."""
    x, y = (int(v) for v in xy)
    cv2.drawMarker(img, (x, y), GREEN, cv2.MARKER_CROSS, 12, 2, cv2.LINE_AA)


def draw_text_strip(img: np.ndarray, text: str, hint: str = "") -> None:
    h = 34 if not hint else 56
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (img.shape[1], h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, dst=img)
    cv2.putText(img, text, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1, cv2.LINE_AA)
    if hint:
        cv2.putText(img, hint, (10, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)
