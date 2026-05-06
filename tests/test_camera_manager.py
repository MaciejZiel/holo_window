import numpy as np

from holowindow.camera.camera_manager import CameraManager
from holowindow.config.settings import CameraSettings


def test_camera_transform_rotates_upside_down_frames():
    manager = CameraManager(CameraSettings(rotate_180=True))
    frame = np.array([[1, 2], [3, 4]], dtype=np.uint8)

    transformed = manager._transform_frame(frame)

    assert transformed.tolist() == [[4, 3], [2, 1]]


def test_camera_transform_label_reflects_runtime_orientation():
    manager = CameraManager(CameraSettings(rotate_180=False))
    assert manager.transform_label == "normal"

    manager.toggle_rotate_180()
    manager.toggle_flip_horizontal()

    assert manager.transform_label == "rotated 180, mirror"


def test_camera_probe_can_use_fixed_index_range():
    manager = CameraManager(CameraSettings(probe_existing_devices_only=False, probe_count=3))

    assert manager._default_probe_indices() == [0, 1, 2]
