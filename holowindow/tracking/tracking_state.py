"""Shared tracking state objects."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class TrackingState:
    """Normalized head tracking state consumed by calibration and rendering."""

    timestamp: float
    face_detected: bool
    head_x: float = 0.0
    head_y: float = 0.0
    head_z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    confidence: float = 0.0
    tracking_lost: bool = False
    source_width: int = 0
    source_height: int = 0
    source_mode: str = "unknown"
    camera_index: int | None = None

    @classmethod
    def neutral(cls, timestamp: float | None = None) -> "TrackingState":
        return cls(
            timestamp=time.monotonic() if timestamp is None else timestamp,
            face_detected=False,
            tracking_lost=False,
        )

    def with_detection_flags(
        self,
        *,
        face_detected: bool,
        tracking_lost: bool,
        confidence: float | None = None,
    ) -> "TrackingState":
        return replace(
            self,
            face_detected=face_detected,
            tracking_lost=tracking_lost,
            confidence=self.confidence if confidence is None else confidence,
        )

