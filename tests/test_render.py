import numpy as np

from render import ROOM_BOXES, draw_room, project


def test_centre_point_projects_to_screen_centre():
    sx, sy = project(np.array([[0.0, 0.0, 4.0]]), cam_x=0.0, cam_y=0.0, size=(640, 480))[0]
    assert (sx, sy) == (320, 240)


def test_near_points_shift_more_than_far_points():
    near = np.array([[0.0, 0.0, 2.0]])
    far = np.array([[0.0, 0.0, 7.0]])
    shift = lambda p: project(p, 0.3, 0.0, (640, 480))[0, 0] - project(p, 0.0, 0.0, (640, 480))[0, 0]
    assert shift(near) < 0 and shift(far) < 0  # leaning right moves the room left
    assert abs(shift(near)) > 2 * abs(shift(far))


def test_boxes_sit_at_different_depths():
    depths = sorted({round(b["center"][2], 1) for b in ROOM_BOXES})
    assert len(depths) == 3


def test_draw_room_draws_something():
    img = np.zeros((480, 640, 3), np.uint8)
    draw_room(img, view=(0.0, 0.0))
    assert img.any()
