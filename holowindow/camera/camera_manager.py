"""OpenCV camera enumeration and capture management."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np

from holowindow.config.settings import CameraSettings

try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except AttributeError:
    pass


@dataclass(frozen=True, slots=True)
class CameraInfo:
    index: int
    name: str
    width: int
    height: int
    fps: float
    mode: str


@dataclass(frozen=True, slots=True)
class CameraFrame:
    image: np.ndarray
    timestamp: float
    camera_index: int
    mode: str


class CameraManager:
    """Handles multiple OpenCV camera devices without assuming a fixed index."""

    def __init__(self, settings: CameraSettings | None = None) -> None:
        self.settings = settings or CameraSettings()
        self.devices: list[CameraInfo] = []
        self.current_index: int | None = None
        self.current_mode: str = "unknown"
        self._capture: cv2.VideoCapture | None = None
        self._failure_count = 0

    @property
    def selected_camera(self) -> CameraInfo | None:
        for device in self.devices:
            if device.index == self.current_index:
                return device
        if self.current_index is None:
            return None
        return CameraInfo(
            index=self.current_index,
            name=f"Camera {self.current_index}",
            width=self.settings.width,
            height=self.settings.height,
            fps=float(self.settings.fps),
            mode=self.current_mode,
        )

    def enumerate_devices(self, indices: Iterable[int] | None = None) -> list[CameraInfo]:
        probe_indices = list(indices) if indices is not None else list(range(self.settings.probe_count))
        discovered: list[CameraInfo] = []

        for index in probe_indices:
            capture = cv2.VideoCapture(index)
            if not capture or not capture.isOpened():
                if capture:
                    capture.release()
                continue

            ok, frame = capture.read()
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.settings.width
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.settings.height
            fps = float(capture.get(cv2.CAP_PROP_FPS)) or float(self.settings.fps)
            mode = self._classify_frame_mode(frame) if ok else "unknown"
            discovered.append(
                CameraInfo(
                    index=index,
                    name=f"Camera {index}",
                    width=width,
                    height=height,
                    fps=fps,
                    mode=mode,
                )
            )
            capture.release()

        self.devices = discovered
        return discovered

    def open(self, index: int) -> bool:
        self.release()
        capture = cv2.VideoCapture(index)
        if not capture or not capture.isOpened():
            if capture:
                capture.release()
            return False

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
        capture.set(cv2.CAP_PROP_FPS, self.settings.fps)

        self._capture = capture
        self.current_index = index
        self.current_mode = "unknown"
        self._failure_count = 0
        if all(device.index != index for device in self.devices):
            self.devices.append(
                CameraInfo(
                    index=index,
                    name=f"Camera {index}",
                    width=self.settings.width,
                    height=self.settings.height,
                    fps=float(self.settings.fps),
                    mode="unknown",
                )
            )
        return True

    def open_first_available(self) -> bool:
        if not self.devices:
            self.enumerate_devices()

        preferred = [self.settings.preferred_index]
        ordered = preferred + [device.index for device in self.devices if device.index not in preferred]
        for index in ordered:
            if self.open(index):
                return True
        return False

    def cycle(self) -> bool:
        if not self.devices:
            self.enumerate_devices()
        if not self.devices:
            return False

        indices = [device.index for device in self.devices]
        if self.current_index not in indices:
            return self.open(indices[0])

        start = indices.index(self.current_index)
        for offset in range(1, len(indices) + 1):
            if self.open(indices[(start + offset) % len(indices)]):
                return True
        return False

    def read(self) -> CameraFrame | None:
        if self._capture is None or not self._capture.isOpened():
            return None

        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._failure_count += 1
            if self._failure_count >= self.settings.failure_limit:
                self.release()
            return None

        self._failure_count = 0
        self.current_mode = self._classify_frame_mode(frame)
        return CameraFrame(
            image=frame,
            timestamp=time.monotonic(),
            camera_index=-1 if self.current_index is None else self.current_index,
            mode=self.current_mode,
        )

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    @staticmethod
    def _classify_frame_mode(frame: np.ndarray | None) -> str:
        if frame is None:
            return "unknown"
        if frame.ndim == 2 or frame.shape[-1] == 1:
            return "IR-like"

        b, g, r = cv2.split(frame[:, :, :3])
        channel_delta = max(
            float(np.mean(np.abs(b.astype(np.int16) - g.astype(np.int16)))),
            float(np.mean(np.abs(g.astype(np.int16) - r.astype(np.int16)))),
        )
        return "IR-like" if channel_delta < 2.0 else "RGB"
