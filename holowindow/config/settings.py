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
    width: int = 1280
    height: int = 720
    fps: int = 30
    failure_limit: int = 10


@dataclass(slots=True)
class TrackingSettings:
    min_detection_confidence: float = 0.55
    min_tracking_confidence: float = 0.5
    smoothing_alpha_position: float = 0.22
    smoothing_alpha_rotation: float = 0.18
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
    parallax_sensitivity: float = 1.0
    sensitivity_x: float = 1.0
    sensitivity_y: float = 1.0
    sensitivity_z: float = 1.0
    rotation_sensitivity: float = 0.45
    camera_lateral_range: float = 2.4
    camera_vertical_range: float = 1.45
    camera_depth_range: float = 1.8
    base_fov: float = 58.0
    min_fov: float = 42.0
    max_fov: float = 72.0
    fullscreen: bool = False
    show_debug: bool = True


@dataclass(slots=True)
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    tracking: TrackingSettings = field(default_factory=TrackingSettings)
    render: RenderSettings = field(default_factory=RenderSettings)
