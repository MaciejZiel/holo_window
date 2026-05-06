"""Runtime settings for HoloWindow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Return *value* constrained to the inclusive range."""
    return max(minimum, min(maximum, value))


@dataclass(slots=True)
class CameraSettings:
    preferred_index: int = 0
    probe_count: int = 8
    probe_existing_devices_only: bool = True
    width: int = 640
    height: int = 360
    fps: int = 60
    buffer_size: int = 1
    failure_limit: int = 10
    threaded_capture: bool = True
    rotate_180: bool = True
    flip_horizontal: bool = False
    flip_vertical: bool = False


@dataclass(slots=True)
class TrackingSettings:
    min_detection_confidence: float = 0.55
    min_tracking_confidence: float = 0.5
    max_tracking_fps: float = 24.0
    processing_width: int = 320
    screen_center_y_in_camera_frame: float = 0.58
    screen_center_x_in_camera_frame: float = 0.5
    smoothing_alpha_position: float = 0.36
    smoothing_alpha_rotation: float = 0.28
    prediction_seconds: float = 0.045
    max_predicted_delta: float = 0.18
    lost_hold_seconds: float = 0.35
    return_to_neutral_alpha: float = 0.045
    max_head_x: float = 1.4
    max_head_y: float = 1.2
    max_head_z: float = 0.9
    max_rotation_degrees: float = 35.0
    calibration_file: Path = Path("holowindow_calibration.json")
    face_landmarker_model_path: Path | None = None
    model_cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "holowindow")
    auto_download_face_model: bool = True
    face_landmarker_model_url: str = (
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
        "face_landmarker/float16/latest/face_landmarker.task"
    )


@dataclass(slots=True)
class RenderSettings:
    parallax_sensitivity: float = 1.6
    sensitivity_x: float = 1.0
    sensitivity_y: float = 1.0
    sensitivity_z: float = 1.0
    rotation_sensitivity: float = 0.45
    camera_lateral_range: float = 3.2
    camera_vertical_range: float = 2.05
    camera_depth_range: float = 1.75
    off_axis_projection: bool = True
    off_axis_motion_exponent: float = 0.62
    virtual_screen_width: float = 11.6
    virtual_screen_height: float = 6.5
    virtual_screen_y: float = 2.1
    virtual_eye_distance: float = 5.2
    min_eye_distance: float = 2.6
    max_eye_distance: float = 8.4
    physical_screen_width_m: float = 0.344
    physical_screen_height_m: float = 0.194
    nominal_eye_distance_m: float = 0.55
    head_lateral_range_m: float = 0.22
    head_vertical_range_m: float = 0.14
    head_depth_range_m: float = 0.24
    projection_depth_scale: float = 0.38
    visual_response_rate: float = 18.0
    visual_jitter_deadzone: float = 0.003
    base_fov: float = 64.0
    min_fov: float = 48.0
    max_fov: float = 76.0
    fullscreen: bool = False
    show_debug: bool = True


@dataclass(slots=True)
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    tracking: TrackingSettings = field(default_factory=TrackingSettings)
    render: RenderSettings = field(default_factory=RenderSettings)
