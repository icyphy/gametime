import sys, types
import numpy as np
import pytest
import importlib

@pytest.fixture
def histogram(monkeypatch):
    stub = types.ModuleType("path")
    class _Path:
        pass
    stub.Path = _Path
    monkeypatch.setitem(sys.modules, "path", stub)

    sys.modules.pop("src.histogram", None)

    import histogram
    return histogram

class DummyPath:
    def __init__(self, predicted_value, measured_value=None):
        self.predicted_value = predicted_value
        self.measured_value = predicted_value if measured_value is None else measured_value

@pytest.fixture
def dummy_paths():
    return [
        DummyPath(1.0),
        DummyPath(2.0),
        DummyPath(2.0, measured_value=5.0),
        DummyPath(3.0),
        DummyPath(4.0),
        DummyPath(5.0),
    ]

@pytest.fixture
def patch_logger(monkeypatch, histogram):
    logger = types.SimpleNamespace(info=lambda *a, **k: None)
    monkeypatch.setattr(histogram, "logger", logger, raising=False)
    return logger

def test_compute_histogram_predicted_basic(histogram, dummy_paths):
    hist, edges = histogram.compute_histogram(dummy_paths, bins=2, path_value_range=None, measured=False)
    assert hist.tolist() == [3, 3]
    assert pytest.approx(edges[0]) == 1.0
    assert pytest.approx(edges[-1]) == 5.0
    assert len(hist) == 2 and len(edges) == 3

def test_compute_histogram_measured_values(histogram, dummy_paths):
    hist, edges = histogram.compute_histogram(dummy_paths, bins=4, path_value_range=(1.0, 5.0), measured=True)
    assert hist.tolist() == [1, 1, 1, 3]
    assert (edges == np.array([1., 2., 3., 4., 5.])).all()

def test_compute_histogram_custom_range(histogram, dummy_paths):
    hist, edges = histogram.compute_histogram(dummy_paths, bins=2, path_value_range=(0.0, 4.0), measured=False)
    assert hist.tolist() == [1, 4]