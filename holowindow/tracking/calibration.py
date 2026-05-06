"""Neutral head-position calibration and sensitivity mapping."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from holowindow.config.settings import TrackingSettings, clamp
from holowindow.tracking.tracking_state import TrackingState


@dataclass(slots=True)
class CalibrationProfile:
    neutral_x: float = 0.0
    neutral_y: float = 0.0
    neutral_z: float = 0.0
    neutral_yaw: float = 0.0
    neutral_pitch: float = 0.0
    neutral_roll: float = 0.0
    sensitivity_x: float = 1.0
    sensitivity_y: float = 1.0
    sensitivity_z: float = 1.0
    rotation_sensitivity: float = 1.0
    calibrated: bool = False


class CalibrationManager:
    """Stores a session neutral pose and maps raw tracker values around it."""

    def __init__(
        self,
        settings: TrackingSettings | None = None,
        profile: CalibrationProfile | None = None,
    ) -> None:
        self.settings = settings or TrackingSettings()
        self.profile = profile or CalibrationProfile()

    @property
    def is_calibrated(self) -> bool:
        return self.profile.calibrated

    def reset(self) -> None:
        self.profile = CalibrationProfile(
            sensitivity_x=self.profile.sensitivity_x,
            sensitivity_y=self.profile.sensitivity_y,
            sensitivity_z=self.profile.sensitivity_z,
            rotation_sensitivity=self.profile.rotation_sensitivity,
        )

    def calibrate(self, state: TrackingState) -> bool:
        if not state.face_detected or state.confidence <= 0.0:
            return False

        self.profile.neutral_x = state.head_x
        self.profile.neutral_y = state.head_y
        self.profile.neutral_z = state.head_z
        self.profile.neutral_yaw = state.yaw
        self.profile.neutral_pitch = state.pitch
        self.profile.neutral_roll = state.roll
        self.profile.calibrated = True
        return True

    def apply(self, state: TrackingState) -> TrackingState:
        if not self.profile.calibrated or not state.face_detected:
            return state

        profile = self.profile
        max_rot = self.settings.max_rotation_degrees
        return replace(
            state,
            head_x=clamp(
                (state.head_x - profile.neutral_x) * profile.sensitivity_x,
                -self.settings.max_head_x,
                self.settings.max_head_x,
            ),
            head_y=clamp(
                (state.head_y - profile.neutral_y) * profile.sensitivity_y,
                -self.settings.max_head_y,
                self.settings.max_head_y,
            ),
            head_z=clamp(
                (state.head_z - profile.neutral_z) * profile.sensitivity_z,
                -self.settings.max_head_z,
                self.settings.max_head_z,
            ),
            yaw=clamp(
                (state.yaw - profile.neutral_yaw) * profile.rotation_sensitivity,
                -max_rot,
                max_rot,
            ),
            pitch=clamp(
                (state.pitch - profile.neutral_pitch) * profile.rotation_sensitivity,
                -max_rot,
                max_rot,
            ),
            roll=clamp(
                (state.roll - profile.neutral_roll) * profile.rotation_sensitivity,
                -max_rot,
                max_rot,
            ),
        )

    def adjust_position_sensitivity(self, delta: float) -> None:
        next_value = clamp(self.profile.sensitivity_x + delta, 0.25, 3.0)
        self.profile.sensitivity_x = next_value
        self.profile.sensitivity_y = next_value
        self.profile.sensitivity_z = next_value

    def adjust_rotation_sensitivity(self, delta: float) -> None:
        self.profile.rotation_sensitivity = clamp(
            self.profile.rotation_sensitivity + delta,
            0.1,
            2.0,
        )

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path is not None else self.settings.calibration_file
        target.write_text(json.dumps(asdict(self.profile), indent=2), encoding="utf-8")

    def load(self, path: str | Path | None = None) -> bool:
        target = Path(path) if path is not None else self.settings.calibration_file
        if not target.exists():
            return False

        data = json.loads(target.read_text(encoding="utf-8"))
        self.profile = CalibrationProfile(**data)
        return True

