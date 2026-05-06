import pytest

from holowindow.config.settings import TrackingSettings
from holowindow.tracking.smoothing import TrackingSmoother
from holowindow.tracking.tracking_state import TrackingState


def detected(timestamp, x=0.0, y=0.0, z=0.0, yaw=0.0):
    return TrackingState(
        timestamp=timestamp,
        face_detected=True,
        head_x=x,
        head_y=y,
        head_z=z,
        yaw=yaw,
        confidence=1.0,
    )


def lost(timestamp):
    return TrackingState(timestamp=timestamp, face_detected=False, tracking_lost=True)


def test_detected_states_are_exponentially_smoothed():
    settings = TrackingSettings(
        smoothing_alpha_position=0.5,
        smoothing_alpha_rotation=0.25,
        prediction_seconds=0.0,
    )
    smoother = TrackingSmoother(settings)

    first = smoother.update(detected(1.0, x=0.0, yaw=0.0), now=1.0)
    second = smoother.update(detected(2.0, x=1.0, yaw=20.0), now=2.0)

    assert first.head_x == 0.0
    assert second.head_x == 0.5
    assert second.yaw == 5.0
    assert second.face_detected
    assert not second.tracking_lost


def test_tracking_loss_holds_last_state_briefly():
    settings = TrackingSettings(lost_hold_seconds=0.5)
    smoother = TrackingSmoother(settings)

    smoother.update(detected(1.0, x=0.8), now=1.0)
    held = smoother.update(lost(1.2), now=1.2)

    assert held.head_x == 0.8
    assert not held.face_detected
    assert held.tracking_lost
    assert held.confidence == 0.0


def test_tracking_loss_eases_back_to_neutral_after_hold():
    settings = TrackingSettings(lost_hold_seconds=0.1, return_to_neutral_alpha=0.25, prediction_seconds=0.0)
    smoother = TrackingSmoother(settings)

    smoother.update(detected(1.0, x=0.8, z=-0.4, yaw=20.0), now=1.0)
    eased = smoother.update(lost(2.0), now=2.0)

    assert eased.head_x == pytest.approx(0.6)
    assert eased.head_z == pytest.approx(-0.3)
    assert eased.yaw == 15.0
    assert eased.tracking_lost


def test_smoother_predicts_short_term_motion():
    settings = TrackingSettings(
        smoothing_alpha_position=1.0,
        smoothing_alpha_rotation=1.0,
        prediction_seconds=0.05,
        max_predicted_delta=0.5,
    )
    smoother = TrackingSmoother(settings)

    smoother.update(detected(1.0, x=0.0), now=1.0)
    predicted = smoother.update(detected(1.1, x=0.2), now=1.1)

    assert predicted.head_x > 0.2
