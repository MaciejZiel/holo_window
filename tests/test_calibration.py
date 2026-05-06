import pytest

from holowindow.config.settings import TrackingSettings
from holowindow.tracking.calibration import CalibrationManager
from holowindow.tracking.tracking_state import TrackingState


def state(**overrides):
    defaults = {
        "timestamp": 1.0,
        "face_detected": True,
        "head_x": 0.1,
        "head_y": 0.2,
        "head_z": 0.3,
        "yaw": 5.0,
        "pitch": -3.0,
        "roll": 1.0,
        "confidence": 0.9,
    }
    defaults.update(overrides)
    return TrackingState(**defaults)


def test_calibration_maps_values_relative_to_neutral():
    calibration = CalibrationManager()
    assert calibration.calibrate(state())

    mapped = calibration.apply(
        state(head_x=-0.2, head_y=0.5, head_z=0.45, yaw=10.0, pitch=-1.0, roll=-2.0)
    )

    assert round(mapped.head_x, 3) == -0.3
    assert round(mapped.head_y, 3) == 0.3
    assert round(mapped.head_z, 3) == 0.5
    assert round(mapped.yaw, 3) == 5.0
    assert round(mapped.pitch, 3) == 2.0
    assert round(mapped.roll, 3) == -3.0


def test_calibration_clamps_extreme_values():
    settings = TrackingSettings(max_head_x=0.5, max_head_y=0.4, max_head_z=0.3, max_rotation_degrees=8.0)
    calibration = CalibrationManager(settings=settings)
    assert calibration.calibrate(state())

    mapped = calibration.apply(state(head_x=10.0, head_y=-10.0, head_z=-10.0, yaw=50.0))

    assert mapped.head_x == 0.5
    assert mapped.head_y == -0.4
    assert mapped.head_z == -0.3
    assert mapped.yaw == 8.0


def test_calibration_ignores_missing_face():
    calibration = CalibrationManager()
    assert not calibration.calibrate(state(face_detected=False, confidence=0.0))
    assert not calibration.is_calibrated


def test_calibration_uses_relative_face_width_for_monocular_depth():
    calibration = CalibrationManager()
    assert calibration.calibrate(state(head_z=0.25))

    closer = calibration.apply(state(head_z=0.30))
    farther = calibration.apply(state(head_z=0.20))

    assert closer.head_z == pytest.approx(0.2)
    assert farther.head_z == pytest.approx(-0.2)
