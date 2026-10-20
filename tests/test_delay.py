import numpy as np
import pytest

from delay import DelayBuffer


def filled(step_ms=10.0, n=30):
    """x moves 1 px per ms, y fixed: easy to check by hand."""
    buf = DelayBuffer()
    for i in range(n):
        t = i * step_ms
        buf.push(t, (t, 5.0))
    return buf


def test_empty_returns_none():
    assert DelayBuffer().at(0) is None


def test_exact_sample():
    np.testing.assert_allclose(filled().at(100), [100, 5])


def test_blends_between_samples():
    np.testing.assert_allclose(filled().at(104.5), [104.5, 5])


def test_100ms_ago():
    buf = filled()
    np.testing.assert_allclose(buf.delayed(now_ms=290, delay_ms=100), [190, 5])


def test_zero_delay_is_newest():
    np.testing.assert_allclose(filled().delayed(290, 0), [290, 5])


@pytest.mark.parametrize("t, expected", [(-50, 0), (1000, 290)])
def test_clamps_outside_range(t, expected):
    np.testing.assert_allclose(filled().at(t), [expected, 5])


def test_old_samples_are_dropped():
    buf = DelayBuffer(keep_ms=100)
    for t in range(0, 500, 10):
        buf.push(t, (t, 0))
    assert len(buf) == 11  # 390..490 inclusive
