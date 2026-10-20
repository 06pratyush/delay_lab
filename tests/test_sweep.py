"""Sweep logic on a synthetic head track: no webcam or MediaPipe needed."""

import numpy as np
import pytest

from sweep import mean_speed_px_per_ms, noise_floor_px, plot, run_sweep


@pytest.fixture(scope="module")
def track():
    # 20 s of smooth side-to-side turns at 30 fps: x swings ±150 px every 2 s.
    t = np.arange(0, 20_000, 1000 / 30)
    x = 320 + 150 * np.sin(2 * np.pi * t / 2000)
    return t, np.column_stack([x, np.full_like(x, 240.0)])


@pytest.fixture(scope="module")
def df(track):
    return run_sweep(*track)


def gaps(df, fix):
    return df[df.fix == fix].set_index("delay_ms").mean_gap_px


def test_zero_delay_has_zero_gap(df):
    assert gaps(df, False)[0] == pytest.approx(0, abs=1e-9)
    assert gaps(df, True)[0] == pytest.approx(0, abs=1e-9)


def test_gap_grows_with_delay_without_fix(df):
    g = gaps(df, False)
    assert g.is_monotonic_increasing
    assert g[100] / g[50] == pytest.approx(2, rel=0.1)  # near-straight line


def test_fix_is_smaller_at_every_delay(df):
    off, on = gaps(df, False), gaps(df, True)
    for d in [25, 50, 75, 100, 150]:
        assert on[d] < off[d] / 2


def test_all_runs_use_the_same_frames(df):
    assert df.frames.nunique() == 1


def test_deterministic(track, df):
    assert run_sweep(*track).equals(df)


def test_skips_frames_without_a_face(track):
    t, nose = track
    nose = nose.copy()
    nose[::7] = np.nan
    out = run_sweep(t, nose)
    assert out.frames.iloc[0] < len(t)


def test_plot_writes_png(tmp_path, track, df):
    out = tmp_path / "sweep.png"
    plot(df, out, mean_speed_px_per_ms(*track))
    assert out.stat().st_size > 10_000


def test_noise_floor_ignores_smooth_motion(track):
    _, nose = track
    assert noise_floor_px(nose) < 0.1


def test_noise_floor_measures_jitter(track):
    _, nose = track
    rng = np.random.default_rng(0)
    noisy = nose + rng.normal(0, 1.0, nose.shape)  # 1 px wobble per axis
    assert noise_floor_px(noisy) == pytest.approx(1.0, rel=0.15)


def test_noise_floor_skips_missing_faces(track):
    _, nose = track
    nose = nose.copy()
    nose[::5] = np.nan  # no run of 7 good frames left
    assert np.isnan(noise_floor_px(nose))
