"""Stable smoothing and tracking-loss behavior for head pose data."""

from __future__ import annotations

import time
from dataclasses import replace

from holowindow.config.settings import TrackingSettings, clamp
from holowindow.tracking.tracking_state import TrackingState


def _ema(current: float, target: float, alpha: float) -> float:
    return current + (target - current) * alpha


class TrackingSmoother:
    """Exponential smoother with short hold and neutral return on lost tracking."""

    def __init__(self, settings: TrackingSettings | None = None) -> None:
        self.settings = settings or TrackingSettings()
        self._state: TrackingState | None = None
        self._last_seen_at: float | None = None
        self._last_update_at: float | None = None
        self._velocity = {
            "head_x": 0.0,
            "head_y": 0.0,
            "head_z": 0.0,
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
        }

    @property
    def current(self) -> TrackingState | None:
        return self._state

    def reset(self) -> None:
        self._state = None
        self._last_seen_at = None
        self._last_update_at = None
        for key in self._velocity:
            self._velocity[key] = 0.0

    def update(
        self,
        measurement: TrackingState,
        now: float | None = None,
    ) -> TrackingState:
        current_time = time.monotonic() if now is None else now
        if measurement.face_detected and measurement.confidence > 0.0:
            self._last_seen_at = current_time
            self._state = self._smooth_detected(measurement, current_time)
            self._last_update_at = current_time
            return self._state

        self._state = self._smooth_lost(measurement, current_time)
        self._last_update_at = current_time
        return self._state

    def adjust_smoothing(self, delta: float) -> None:
        next_position = clamp(self.settings.smoothing_alpha_position + delta, 0.04, 0.9)
        next_rotation = clamp(self.settings.smoothing_alpha_rotation + delta, 0.04, 0.9)
        self.settings.smoothing_alpha_position = next_position
        self.settings.smoothing_alpha_rotation = next_rotation

    def _smooth_detected(self, measurement: TrackingState, current_time: float) -> TrackingState:
        if self._state is None:
            return measurement.with_detection_flags(
                face_detected=True,
                tracking_lost=False,
                confidence=measurement.confidence,
            )

        pos_alpha = self.settings.smoothing_alpha_position
        rot_alpha = self.settings.smoothing_alpha_rotation
        smoothed = replace(
            measurement,
            face_detected=True,
            tracking_lost=False,
            head_x=_ema(self._state.head_x, measurement.head_x, pos_alpha),
            head_y=_ema(self._state.head_y, measurement.head_y, pos_alpha),
            head_z=_ema(self._state.head_z, measurement.head_z, pos_alpha),
            yaw=_ema(self._state.yaw, measurement.yaw, rot_alpha),
            pitch=_ema(self._state.pitch, measurement.pitch, rot_alpha),
            roll=_ema(self._state.roll, measurement.roll, rot_alpha),
            confidence=_ema(self._state.confidence, measurement.confidence, 0.35),
        )
        self._update_velocity(self._state, smoothed, current_time)
        return self._predict(smoothed)

    def _update_velocity(self, previous: TrackingState, current: TrackingState, current_time: float) -> None:
        if self._last_update_at is None:
            return
        dt = max(1e-3, current_time - self._last_update_at)
        velocity_alpha = 0.35
        for field in self._velocity:
            sample = (getattr(current, field) - getattr(previous, field)) / dt
            self._velocity[field] = _ema(self._velocity[field], sample, velocity_alpha)

    def _predict(self, state: TrackingState) -> TrackingState:
        horizon = self.settings.prediction_seconds
        if horizon <= 0.0:
            return state
        max_delta = self.settings.max_predicted_delta

        def predicted(field: str) -> float:
            delta = clamp(self._velocity[field] * horizon, -max_delta, max_delta)
            return getattr(state, field) + delta

        return replace(
            state,
            head_x=predicted("head_x"),
            head_y=predicted("head_y"),
            head_z=predicted("head_z"),
            yaw=predicted("yaw"),
            pitch=predicted("pitch"),
            roll=predicted("roll"),
        )

    def _smooth_lost(
        self,
        measurement: TrackingState,
        current_time: float,
    ) -> TrackingState:
        if self._state is None:
            return replace(
                TrackingState.neutral(timestamp=measurement.timestamp),
                source_width=measurement.source_width,
                source_height=measurement.source_height,
                source_mode=measurement.source_mode,
                camera_index=measurement.camera_index,
                tracking_lost=True,
            )

        if (
            self._last_seen_at is not None
            and current_time - self._last_seen_at <= self.settings.lost_hold_seconds
        ):
            return replace(
                self._state,
                timestamp=measurement.timestamp,
                face_detected=False,
                tracking_lost=True,
                confidence=0.0,
                source_width=measurement.source_width or self._state.source_width,
                source_height=measurement.source_height or self._state.source_height,
                source_mode=measurement.source_mode,
                camera_index=measurement.camera_index,
            )

        alpha = self.settings.return_to_neutral_alpha
        return replace(
            self._state,
            timestamp=measurement.timestamp,
            face_detected=False,
            tracking_lost=True,
            head_x=_ema(self._state.head_x, 0.0, alpha),
            head_y=_ema(self._state.head_y, 0.0, alpha),
            head_z=_ema(self._state.head_z, 0.0, alpha),
            yaw=_ema(self._state.yaw, 0.0, alpha),
            pitch=_ema(self._state.pitch, 0.0, alpha),
            roll=_ema(self._state.roll, 0.0, alpha),
            confidence=0.0,
            source_width=measurement.source_width or self._state.source_width,
            source_height=measurement.source_height or self._state.source_height,
            source_mode=measurement.source_mode,
            camera_index=measurement.camera_index,
        )
