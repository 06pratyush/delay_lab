"""Drawing: the AR sticker, the VR-style wireframe room and the text strip."""

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


# --- VR-style room ---------------------------------------------------------
# World units are metres; x right, y up, z into the screen. The viewer looks
# through the laptop screen as if it were a window, from about 0 m depth.

FLOOR_Y = -1.0
GRID_X = np.linspace(-3, 3, 13)
GRID_Z = np.linspace(1.5, 10, 18)
ROOM_BOXES = [  # near, middle, far: parallax makes the near one move most
    {"center": (-1.2, FLOOR_Y + 0.35, 2.5), "size": 0.7, "color": (80, 80, 255)},
    {"center": (1.0, FLOOR_Y + 0.6, 4.5), "size": 1.2, "color": (80, 220, 255)},
    {"center": (-0.2, FLOOR_Y + 1.0, 7.5), "size": 2.0, "color": (255, 180, 80)},
]
_CUBE = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)])
_CUBE_EDGES = [(a, b) for a in range(8) for b in range(a + 1, 8)
               if np.sum(np.abs(_CUBE[a] - _CUBE[b])) == 1]


def project(points: np.ndarray, cam_x: float, cam_y: float, size) -> np.ndarray:
    """Pinhole projection: screen offset = sideways offset / depth, scaled to the window."""
    w, h = size
    f = 0.8 * w
    x, y, z = points[:, 0] - cam_x, points[:, 1] - cam_y, points[:, 2]
    sx = w / 2 + f * x / z
    sy = h / 2 - f * y / z
    return np.round(np.column_stack([sx, sy])).astype(int)


def view_from_nose(nose_xy, size) -> tuple[float, float]:
    """Nose position in the (mirrored) image -> viewer position in metres."""
    w, h = size
    return (float(nose_xy[0]) - w / 2) / (w / 2) * 0.8, -(float(nose_xy[1]) - h / 2) / (h / 2) * 0.5


def draw_room(img: np.ndarray, view: tuple[float, float]) -> None:
    size = (img.shape[1], img.shape[0])
    cx, cy = view
    grid = (70, 70, 70)
    for x in GRID_X:
        a, b = project(np.array([[x, FLOOR_Y, GRID_Z[0]], [x, FLOOR_Y, GRID_Z[-1]]]), cx, cy, size)
        cv2.line(img, tuple(a), tuple(b), grid, 1, cv2.LINE_AA)
    for z in GRID_Z:
        a, b = project(np.array([[GRID_X[0], FLOOR_Y, z], [GRID_X[-1], FLOOR_Y, z]]), cx, cy, size)
        cv2.line(img, tuple(a), tuple(b), grid, 1, cv2.LINE_AA)
    for box in sorted(ROOM_BOXES, key=lambda b: -b["center"][2]):  # far first
        pts = project(_CUBE * box["size"] + np.array(box["center"]), cx, cy, size)
        for a, b in _CUBE_EDGES:
            cv2.line(img, tuple(pts[a]), tuple(pts[b]), box["color"], 2, cv2.LINE_AA)


def draw_text_strip(img: np.ndarray, text: str, hint: str = "") -> None:
    h = 34 if not hint else 56
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (img.shape[1], h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, dst=img)
    cv2.putText(img, text, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1, cv2.LINE_AA)
    if hint:
        cv2.putText(img, hint, (10, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)
