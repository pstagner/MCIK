import pytest
from experiments.ascii_torus.python.metrics import estimate_ascii_quality

def test_ascii_quality_deterministic():
    w, h = 8, 4
    buf = [" "] * (w * h)
    for x in range(w):
        buf[(h // 2) * w + x] = "#"
    q1 = estimate_ascii_quality(buf, w, h)
    q2 = estimate_ascii_quality(buf, w, h)
    assert q1 == pytest.approx(q2)
