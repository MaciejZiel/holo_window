import numpy as np

from holowindow.config.settings import TrackingSettings
from holowindow.tracking.face_tracker import FaceTracker


def tracker_without_backend(settings):
    tracker = object.__new__(FaceTracker)
    tracker.settings = settings
    return tracker


def test_tracking_resize_preserves_aspect_ratio():
    tracker = tracker_without_backend(TrackingSettings(processing_width=320))
    frame = np.zeros((360, 640, 3), dtype=np.uint8)

    resized = tracker._resize_for_tracking(frame)

    assert resized.shape == (180, 320, 3)


def test_tracking_resize_skips_small_frames():
    tracker = tracker_without_backend(TrackingSettings(processing_width=640))
    frame = np.zeros((180, 320, 3), dtype=np.uint8)

    resized = tracker._resize_for_tracking(frame)

    assert resized is frame
