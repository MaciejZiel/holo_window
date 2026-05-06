"""MediaPipe Face Mesh based head-pose tracker."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import urllib.request
from typing import Sequence

import cv2
import numpy as np

from holowindow.config.settings import TrackingSettings, clamp
from holowindow.tracking.tracking_state import TrackingState


@dataclass(frozen=True, slots=True)
class LandmarkPoint:
    x: int
    y: int


class FaceTracker:
    """Tracks robust head pose from face landmarks without relying on pupils."""

    _POSE_LANDMARKS = (1, 152, 33, 263, 61, 291)
    _MODEL_POINTS = np.array(
        [
            (0.0, 0.0, 0.0),  # nose tip
            (0.0, -63.6, -12.5),  # chin
            (-43.3, 32.7, -26.0),  # left eye outer corner
            (43.3, 32.7, -26.0),  # right eye outer corner
            (-28.9, -28.9, -24.1),  # left mouth corner
            (28.9, -28.9, -24.1),  # right mouth corner
        ],
        dtype=np.float64,
    )
    _CENTER_LANDMARKS = (1, 4, 10, 152, 234, 454, 61, 291)
    _DEBUG_LANDMARKS = (1, 10, 33, 61, 152, 234, 263, 291, 454)

    def __init__(self, settings: TrackingSettings | None = None) -> None:
        self.settings = settings or TrackingSettings()
        self._last_landmarks: Sequence[object] | None = None
        self._last_bbox: tuple[int, int, int, int] | None = None
        self._backend = "unavailable"
        self._face_mesh: object | None = None
        self._task_landmarker: object | None = None
        self._task_image_cls: object | None = None
        self._task_image_format: object | None = None
        self._last_task_timestamp_ms = 0
        self._haar: cv2.CascadeClassifier | None = None
        self._create_backend()

    @property
    def available(self) -> bool:
        return self._backend != "unavailable"

    @property
    def backend_name(self) -> str:
        return self._backend

    def process_frame(
        self,
        frame: np.ndarray | None,
        *,
        timestamp: float,
        camera_index: int | None = None,
        source_mode: str = "unknown",
    ) -> TrackingState:
        if frame is None:
            return TrackingState.neutral(timestamp=timestamp)
        source_height, source_width = frame.shape[:2]
        frame = self._resize_for_tracking(frame)
        height, width = frame.shape[:2]

        if not self.available:
            return TrackingState(
                timestamp=timestamp,
                face_detected=False,
                confidence=0.0,
                tracking_lost=True,
                source_width=source_width,
                source_height=source_height,
                source_mode=source_mode,
                camera_index=camera_index,
            )

        rgb = self._to_rgb(frame)
        landmarks = self._detect_landmarks(rgb, timestamp=timestamp)
        if landmarks is None and self._backend == "haar_fallback":
            return self._process_haar(
                frame,
                timestamp=timestamp,
                camera_index=camera_index,
                source_mode=source_mode,
            )

        if landmarks is None:
            self._last_landmarks = None
            self._last_bbox = None
            return TrackingState(
                timestamp=timestamp,
                face_detected=False,
                confidence=0.0,
                tracking_lost=True,
                source_width=source_width,
                source_height=source_height,
                source_mode=source_mode,
                camera_index=camera_index,
            )

        self._last_landmarks = landmarks
        self._last_bbox = None
        state = self._state_from_landmarks(
            landmarks,
            width=width,
            height=height,
            source_width=source_width,
            source_height=source_height,
            timestamp=timestamp,
            source_mode=source_mode,
            camera_index=camera_index,
        )
        return state

    def draw_debug(self, frame: np.ndarray) -> np.ndarray:
        if self._last_landmarks is None:
            if self._last_bbox is None:
                return frame
            annotated = self._ensure_bgr(frame)
            x, y, w, h = self._last_bbox
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 210), 2)
            cv2.circle(annotated, (x + w // 2, y + h // 2), 4, (0, 255, 210), -1)
            return annotated

        annotated = self._ensure_bgr(frame)
        height, width = annotated.shape[:2]
        points = [self._landmark_to_pixel(self._last_landmarks[index], width, height) for index in self._DEBUG_LANDMARKS]
        valid = [point for point in points if point is not None]
        if not valid:
            return annotated

        xs = [point.x for point in valid]
        ys = [point.y for point in valid]
        cv2.rectangle(
            annotated,
            (max(0, min(xs) - 16), max(0, min(ys) - 16)),
            (min(width - 1, max(xs) + 16), min(height - 1, max(ys) + 16)),
            (0, 255, 210),
            2,
        )
        for point in valid:
            cv2.circle(annotated, (point.x, point.y), 3, (0, 255, 210), -1)
        return annotated

    def close(self) -> None:
        if self._face_mesh is not None:
            self._face_mesh.close()
        if self._task_landmarker is not None:
            close = getattr(self._task_landmarker, "close", None)
            if callable(close):
                close()

    def _create_backend(self) -> None:
        self._face_mesh = self._create_legacy_face_mesh()
        if self._face_mesh is not None:
            self._backend = "mediapipe_face_mesh"
            return

        self._task_landmarker = self._create_task_landmarker()
        if self._task_landmarker is not None:
            self._backend = "mediapipe_face_landmarker"
            return

        self._haar = self._create_haar_fallback()
        if self._haar is not None:
            self._backend = "haar_fallback"

    def _create_legacy_face_mesh(self) -> object | None:
        try:
            import mediapipe as mp
            face_mesh_module = mp.solutions.face_mesh
        except (AttributeError, ImportError):
            return None

        return face_mesh_module.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=self.settings.min_detection_confidence,
            min_tracking_confidence=self.settings.min_tracking_confidence,
        )

    def _create_task_landmarker(self) -> object | None:
        model_path = self._resolve_task_model()
        if model_path is None:
            return None

        os.environ.setdefault("GLOG_minloglevel", "2")
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError:
            return None

        self._task_image_cls = mp.Image
        self._task_image_format = mp.ImageFormat.SRGB
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=self.settings.min_detection_confidence,
            min_face_presence_confidence=self.settings.min_detection_confidence,
            min_tracking_confidence=self.settings.min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        try:
            return vision.FaceLandmarker.create_from_options(options)
        except Exception:
            return None

    def _resolve_task_model(self) -> Path | None:
        env_path = os.getenv("HOLOWINDOW_FACE_LANDMARKER_MODEL")
        if env_path:
            path = Path(env_path).expanduser()
            return path if path.exists() else None

        configured = self.settings.face_landmarker_model_path
        if configured is not None:
            path = configured.expanduser()
            return path if path.exists() else None

        target = self.settings.model_cache_dir / "face_landmarker.task"
        if target.exists():
            return target
        if not self.settings.auto_download_face_model:
            return None

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(self.settings.face_landmarker_model_url, timeout=12) as response:
                target.write_bytes(response.read())
        except Exception:
            return None
        return target if target.exists() else None

    @staticmethod
    def _create_haar_fallback() -> cv2.CascadeClassifier | None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        classifier = cv2.CascadeClassifier(path)
        return classifier if not classifier.empty() else None

    @staticmethod
    def _to_rgb(frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        if frame.shape[-1] == 1:
            return cv2.cvtColor(frame[:, :, 0], cv2.COLOR_GRAY2RGB)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _resize_for_tracking(self, frame: np.ndarray) -> np.ndarray:
        target_width = self.settings.processing_width
        if target_width <= 0 or frame.shape[1] <= target_width:
            return frame
        scale = target_width / frame.shape[1]
        target_height = max(1, int(frame.shape[0] * scale))
        return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _ensure_bgr(frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if frame.shape[-1] == 1:
            return cv2.cvtColor(frame[:, :, 0], cv2.COLOR_GRAY2BGR)
        return frame.copy()

    def _detect_landmarks(self, rgb: np.ndarray, *, timestamp: float) -> Sequence[object] | None:
        if self._backend == "mediapipe_face_mesh" and self._face_mesh is not None:
            result = self._face_mesh.process(rgb)
            if result.multi_face_landmarks:
                return result.multi_face_landmarks[0].landmark
            return None

        if self._backend == "mediapipe_face_landmarker" and self._task_landmarker is not None:
            image = self._task_image_cls(image_format=self._task_image_format, data=rgb)
            result = self._task_landmarker.detect_for_video(image, self._timestamp_ms(timestamp))
            if result.face_landmarks:
                return result.face_landmarks[0]
        return None

    def _timestamp_ms(self, timestamp: float) -> int:
        timestamp_ms = int(timestamp * 1000.0)
        if timestamp_ms <= self._last_task_timestamp_ms:
            timestamp_ms = self._last_task_timestamp_ms + 1
        self._last_task_timestamp_ms = timestamp_ms
        return timestamp_ms

    def _process_haar(
        self,
        frame: np.ndarray,
        *,
        timestamp: float,
        camera_index: int | None,
        source_mode: str,
    ) -> TrackingState:
        if self._haar is None:
            return TrackingState.neutral(timestamp=timestamp)

        gray = frame if frame.ndim == 2 else cv2.cvtColor(self._ensure_bgr(frame), cv2.COLOR_BGR2GRAY)
        faces = self._haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(72, 72))
        height, width = gray.shape[:2]
        if len(faces) == 0:
            self._last_bbox = None
            return TrackingState(
                timestamp=timestamp,
                face_detected=False,
                confidence=0.0,
                tracking_lost=True,
                source_width=width,
                source_height=height,
                source_mode=source_mode,
                camera_index=camera_index,
            )

        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        self._last_bbox = (int(x), int(y), int(w), int(h))
        self._last_landmarks = None
        face_width = w / max(1, width)
        confidence = clamp((face_width - 0.08) / 0.20, 0.15, 0.72)
        return TrackingState(
            timestamp=timestamp,
            face_detected=True,
            tracking_lost=False,
            head_x=clamp(((x + w * 0.5) / width - 0.5) * 2.0, -1.5, 1.5),
            head_y=clamp((0.5 - (y + h * 0.45) / height) * 2.0, -1.5, 1.5),
            head_z=clamp(face_width, 0.0, 1.5),
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            confidence=confidence,
            source_width=width,
            source_height=height,
            source_mode=source_mode,
            camera_index=camera_index,
        )

    def _state_from_landmarks(
        self,
        landmarks: Sequence[object],
        *,
        width: int,
        height: int,
        source_width: int,
        source_height: int,
        timestamp: float,
        source_mode: str,
        camera_index: int | None,
    ) -> TrackingState:
        center = self._weighted_face_center(landmarks)
        face_width = abs(landmarks[454].x - landmarks[234].x)
        confidence = clamp((face_width - 0.08) / 0.18, 0.0, 1.0)

        yaw = pitch = roll = 0.0
        image_points = self._pose_image_points(landmarks, width, height)
        if image_points is not None:
            pose = self._estimate_euler_angles(image_points, width, height)
            if pose is not None:
                pitch, yaw, roll = pose
                confidence = max(confidence, 0.65)

        return TrackingState(
            timestamp=timestamp,
            face_detected=True,
            tracking_lost=False,
            head_x=clamp((center[0] - self.settings.screen_center_x_in_camera_frame) * 2.0, -1.5, 1.5),
            head_y=clamp((self.settings.screen_center_y_in_camera_frame - center[1]) * 2.0, -1.5, 1.5),
            head_z=clamp(face_width, 0.0, 1.5),
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            confidence=confidence,
            source_width=source_width,
            source_height=source_height,
            source_mode=source_mode,
            camera_index=camera_index,
        )

    def _pose_image_points(
        self,
        landmarks: Sequence[object],
        width: int,
        height: int,
    ) -> np.ndarray | None:
        points: list[tuple[float, float]] = []
        for index in self._POSE_LANDMARKS:
            point = self._landmark_to_pixel(landmarks[index], width, height)
            if point is None:
                return None
            points.append((float(point.x), float(point.y)))
        return np.array(points, dtype=np.float64)

    def _estimate_euler_angles(
        self,
        image_points: np.ndarray,
        width: int,
        height: int,
    ) -> tuple[float, float, float] | None:
        focal_length = float(width)
        camera_matrix = np.array(
            [
                [focal_length, 0.0, width / 2.0],
                [0.0, focal_length, height / 2.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        distortion = np.zeros((4, 1), dtype=np.float64)
        success, rotation_vec, _translation_vec = cv2.solvePnP(
            self._MODEL_POINTS,
            image_points,
            camera_matrix,
            distortion,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return None

        rotation_matrix, _ = cv2.Rodrigues(rotation_vec)
        angles, *_ = cv2.RQDecomp3x3(rotation_matrix)
        pitch, yaw, roll = (float(angle) for angle in angles)
        max_rot = self.settings.max_rotation_degrees
        return (
            clamp(pitch, -max_rot, max_rot),
            clamp(yaw, -max_rot, max_rot),
            clamp(roll, -max_rot, max_rot),
        )

    @classmethod
    def _weighted_face_center(cls, landmarks: Sequence[object]) -> tuple[float, float]:
        xs = [float(landmarks[index].x) for index in cls._CENTER_LANDMARKS]
        ys = [float(landmarks[index].y) for index in cls._CENTER_LANDMARKS]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    @staticmethod
    def _landmark_to_pixel(landmark: object, width: int, height: int) -> LandmarkPoint | None:
        x = int(float(landmark.x) * width)
        y = int(float(landmark.y) * height)
        if x < 0 or y < 0 or x >= width or y >= height:
            return None
        return LandmarkPoint(x=x, y=y)
