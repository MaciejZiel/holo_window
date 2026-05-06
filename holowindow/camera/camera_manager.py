"""OpenCV camera enumeration and capture management."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread
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
        self._latest_frame: CameraFrame | None = None
        self._latest_lock = Lock()
        self._stop_reader = Event()
        self._reader_thread: Thread | None = None

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

    @property
    def transform_label(self) -> str:
        transforms: list[str] = []
        if self.settings.rotate_180:
            transforms.append("rotated 180")
        if self.settings.flip_horizontal:
            transforms.append("mirror")
        if self.settings.flip_vertical:
            transforms.append("flip V")
        return ", ".join(transforms) if transforms else "normal"

    def enumerate_devices(self, indices: Iterable[int] | None = None) -> list[CameraInfo]:
        probe_indices = list(indices) if indices is not None else self._default_probe_indices()
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

    def _default_probe_indices(self) -> list[int]:
        if self.settings.probe_existing_devices_only:
            video_devices = sorted(Path("/dev").glob("video*"))
            indices: list[int] = []
            for device in video_devices:
                suffix = device.name.removeprefix("video")
                if suffix.isdigit():
                    indices.append(int(suffix))
            if indices:
                return indices[: self.settings.probe_count]
        return list(range(self.settings.probe_count))

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
        capture.set(cv2.CAP_PROP_BUFFERSIZE, self.settings.buffer_size)

        self._capture = capture
        self.current_index = index
        self.current_mode = "unknown"
        self._failure_count = 0
        self._latest_frame = None
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
        if self.settings.threaded_capture:
            self._start_reader_thread()
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
        if self.settings.threaded_capture:
            with self._latest_lock:
                return self._latest_frame
        return self._read_direct()

    def toggle_rotate_180(self) -> bool:
        self.settings.rotate_180 = not self.settings.rotate_180
        self._clear_latest_frame()
        return self.settings.rotate_180

    def toggle_flip_horizontal(self) -> bool:
        self.settings.flip_horizontal = not self.settings.flip_horizontal
        self._clear_latest_frame()
        return self.settings.flip_horizontal

    def toggle_flip_vertical(self) -> bool:
        self.settings.flip_vertical = not self.settings.flip_vertical
        self._clear_latest_frame()
        return self.settings.flip_vertical

    def release(self) -> None:
        self._stop_reader.set()
        if self._reader_thread is not None and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.7)
        self._reader_thread = None
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        with self._latest_lock:
            self._latest_frame = None

    def _start_reader_thread(self) -> None:
        self._stop_reader.clear()
        self._reader_thread = Thread(target=self._reader_loop, name="holowindow-camera-reader", daemon=True)
        self._reader_thread.start()

    def _clear_latest_frame(self) -> None:
        with self._latest_lock:
            self._latest_frame = None

    def _reader_loop(self) -> None:
        while not self._stop_reader.is_set():
            frame = self._read_direct()
            if frame is not None:
                with self._latest_lock:
                    self._latest_frame = frame
            else:
                time.sleep(0.006)

    def _read_direct(self) -> CameraFrame | None:
        if self._capture is None or not self._capture.isOpened():
            return None

        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._failure_count += 1
            if self._failure_count >= self.settings.failure_limit:
                if self.settings.threaded_capture:
                    self._stop_reader.set()
                else:
                    self.release()
            return None

        self._failure_count = 0
        frame = self._transform_frame(frame)
        self.current_mode = self._classify_frame_mode(frame)
        return CameraFrame(
            image=frame,
            timestamp=time.monotonic(),
            camera_index=-1 if self.current_index is None else self.current_index,
            mode=self.current_mode,
        )

    def _transform_frame(self, frame: np.ndarray) -> np.ndarray:
        if self.settings.rotate_180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        if self.settings.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.settings.flip_vertical:
            frame = cv2.flip(frame, 0)
        return frame

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
