"""Physical off-axis projection mapping inspired by Parallax Window."""

from __future__ import annotations

from dataclasses import dataclass

from holowindow.config.settings import RenderSettings, clamp


@dataclass(frozen=True, slots=True)
class EyePoseUnits:
    x: float
    z: float
    distance: float
    screen_width: float
    screen_height: float


def physical_eye_pose_units(
    *,
    head_x: float,
    head_y: float,
    head_z: float,
    parallax: float,
    settings: RenderSettings,
) -> EyePoseUnits:
    """Map normalized calibrated head motion into screen-space units.

    The source project describes the projection in physical meters: screen size,
    head offset from screen center, and eye distance from the screen. Panda3D can
    use any consistent unit, so we scale meters so the configured screen height
    matches the existing scene scale.
    """
    physical_height = max(0.05, settings.physical_screen_height_m)
    scale = settings.virtual_screen_height / physical_height
    screen_width = max(0.05, settings.physical_screen_width_m) * scale
    screen_height = settings.virtual_screen_height

    x = head_x * settings.head_lateral_range_m * scale * settings.sensitivity_x * parallax
    z = head_y * settings.head_vertical_range_m * scale * settings.sensitivity_y * parallax
    distance_m = settings.nominal_eye_distance_m - head_z * settings.head_depth_range_m * settings.sensitivity_z
    distance = distance_m * scale * settings.projection_depth_scale

    return EyePoseUnits(
        x=clamp(x, -screen_width * 0.82, screen_width * 0.82),
        z=clamp(z, -screen_height * 0.82, screen_height * 0.82),
        distance=clamp(distance, settings.min_eye_distance, settings.max_eye_distance),
        screen_width=screen_width,
        screen_height=screen_height,
    )


def off_axis_frustum_corners(eye: EyePoseUnits) -> tuple[tuple[float, float, float], ...]:
    """Return upper-left, upper-right, lower-left, lower-right corners."""
    half_w = eye.screen_width / 2.0
    half_h = eye.screen_height / 2.0
    return (
        (-half_w - eye.x, eye.distance, half_h - eye.z),
        (half_w - eye.x, eye.distance, half_h - eye.z),
        (-half_w - eye.x, eye.distance, -half_h - eye.z),
        (half_w - eye.x, eye.distance, -half_h - eye.z),
    )
