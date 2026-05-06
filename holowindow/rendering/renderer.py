"""Panda3D application renderer and runtime loop."""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from math import exp

from holowindow.config.settings import AppSettings, clamp
from holowindow.rendering.projection import off_axis_frustum_corners, physical_eye_pose_units
from holowindow.tracking.tracking_state import TrackingState


class MissingRenderDependencyError(RuntimeError):
    """Raised when Panda3D is not installed."""


try:
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import (
        AmbientLight,
        AntialiasAttrib,
        DirectionalLight,
        Lens,
        NodePath,
        PerspectiveLens,
        PointLight,
        Vec3,
        Vec4,
        WindowProperties,
        loadPrcFileData,
    )
except ImportError as exc:  # pragma: no cover - exercised by real startup only.
    ShowBase = object  # type: ignore[assignment,misc]
    _PANDA_IMPORT_ERROR = exc
else:
    _PANDA_IMPORT_ERROR = None


class HoloWindowRenderer(ShowBase):
    """Owns the Panda3D window, scenes, controls, and per-frame tracking loop."""

    def __init__(self, runtime: "HoloWindowRuntime") -> None:
        if _PANDA_IMPORT_ERROR is not None:
            raise MissingRenderDependencyError(
                "Panda3D is required. Install dependencies with: python -m pip install -r requirements.txt"
            ) from _PANDA_IMPORT_ERROR

        loadPrcFileData("", "window-title HoloWindow")
        loadPrcFileData("", "framebuffer-multisample 1")
        loadPrcFileData("", "multisamples 4")
        loadPrcFileData("", "sync-video true")
        loadPrcFileData("", "show-frame-rate-meter false")

        super().__init__()
        self.runtime = runtime
        self.settings: AppSettings = runtime.settings
        self.disableMouse()
        self.setBackgroundColor(0.005, 0.008, 0.018, 1.0)
        self.render.setAntialias(AntialiasAttrib.MAuto)

        self._last_time = time.monotonic()
        self._last_frame_bgr = None
        self._last_tracking = TrackingState.neutral()
        self._visual_tracking = TrackingState.neutral()
        self._current_scene_index = 0
        self._scenes = self._create_scenes()
        self._scene_root = self.render.attachNewNode("scene-root")
        self._active_scene = None
        self._setup_camera()
        self._setup_lighting()

        from holowindow.ui.debug_overlay import DebugOverlay

        self.overlay = DebugOverlay(self.aspect2d)
        self.overlay.set_visible(self.settings.render.show_debug)
        self._setup_controls()
        self.switch_scene(0)
        self.taskMgr.add(self._update_task, "holowindow-update")

    @property
    def active_scene_name(self) -> str:
        return self._scenes[self._current_scene_index].name

    def switch_scene(self, index: int) -> None:
        index = max(0, min(len(self._scenes) - 1, index))
        if self._active_scene is not None:
            self._active_scene.destroy()
        self._current_scene_index = index
        self._active_scene = self._scenes[index]
        self._active_scene.setup(self._scene_root)

    def quit(self) -> None:
        self.runtime.close()
        self.userExit()

    def _create_scenes(self):
        from holowindow.rendering.scenes import (
            HolographicGalleryScene,
            NeonWallPortalScene,
            ReferenceCubeScene,
            StarTunnelScene,
        )

        return [NeonWallPortalScene(), StarTunnelScene(), HolographicGalleryScene(), ReferenceCubeScene()]

    def _setup_camera(self) -> None:
        lens = PerspectiveLens()
        lens.setFov(self.settings.render.base_fov)
        lens.setNearFar(0.08, 75.0)
        self.cam.node().setLens(lens)
        self.camera.setPos(0, -4.8, 0)
        self.camera.lookAt(0, 4.8, 0)

    def _setup_lighting(self) -> None:
        ambient = AmbientLight("ambient-neon-fill")
        ambient.setColor(Vec4(0.09, 0.12, 0.18, 1.0))
        self.render.setLight(self.render.attachNewNode(ambient))

        key = DirectionalLight("key-light")
        key.setColor(Vec4(0.32, 0.48, 0.72, 1.0))
        key_path = self.render.attachNewNode(key)
        key_path.setHpr(-35, -38, 0)
        self.render.setLight(key_path)

        cyan = PointLight("cyan-glow")
        cyan.setColor(Vec4(0.1, 0.9, 1.0, 1.0))
        cyan_path = self.render.attachNewNode(cyan)
        cyan_path.setPos(-2.0, 2.8, 1.6)
        self.render.setLight(cyan_path)

        magenta = PointLight("magenta-glow")
        magenta.setColor(Vec4(0.95, 0.18, 1.0, 1.0))
        magenta_path = self.render.attachNewNode(magenta)
        magenta_path.setPos(2.2, 4.8, -1.1)
        self.render.setLight(magenta_path)

    def _setup_controls(self) -> None:
        self.accept("escape", self.quit)
        self.accept("c", self._calibrate)
        self.accept("r", self._reset_tracking)
        self.accept("d", self.overlay.toggle)
        self.accept("f", self._toggle_fullscreen)
        self.accept("tab", self._cycle_camera)
        self.accept("u", self._toggle_camera_rotate)
        self.accept("m", self._toggle_camera_mirror)
        self.accept("v", self._toggle_camera_vertical_flip)
        self.accept("p", self._toggle_off_axis_projection)
        self.accept("1", self.switch_scene, [0])
        self.accept("2", self.switch_scene, [1])
        self.accept("3", self.switch_scene, [2])
        self.accept("4", self.switch_scene, [3])
        self.accept("+", self._adjust_parallax, [0.1])
        self.accept("=", self._adjust_parallax, [0.1])
        self.accept("-", self._adjust_parallax, [-0.1])
        self.accept("[", self._adjust_smoothing, [-0.03])
        self.accept("]", self._adjust_smoothing, [0.03])

    def _update_task(self, task):
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self._last_time))
        self._last_time = now

        self.runtime.debug_preview_enabled = self.overlay.visible
        tracking = self.runtime.update_tracking()
        self._last_tracking = tracking
        self._last_frame_bgr = self.runtime.debug_frame
        self._visual_tracking = self._smooth_visual_tracking(self._visual_tracking, tracking, dt)
        self._apply_head_tracked_camera(self._visual_tracking)
        if self._active_scene is not None:
            self._active_scene.update(dt, task.time)
        self._update_overlay()
        return task.cont

    def _apply_head_tracked_camera(self, state: TrackingState) -> None:
        render = self.settings.render
        x_head = self._amplify_head_motion(state.head_x)
        y_head = self._amplify_head_motion(state.head_y)
        z_head = self._amplify_head_motion(state.head_z)
        parallax = render.parallax_sensitivity * (1.0 + clamp(z_head, -0.6, 0.8) * 0.42)
        x = x_head * render.camera_lateral_range * render.sensitivity_x * parallax
        z = y_head * render.camera_vertical_range * render.sensitivity_y * parallax
        if render.off_axis_projection:
            self._apply_off_axis_camera(state, x_head, y_head, z_head, parallax)
            return

        y = -4.8 + z_head * render.camera_depth_range * render.sensitivity_z
        x = clamp(x, -3.8, 3.8)
        y = clamp(y, -6.4, -3.35)
        z = clamp(z, -2.4, 2.4)

        self.camera.setPos(x, y, z)
        target = Vec3(
            state.yaw * 0.015 * render.rotation_sensitivity,
            4.8,
            state.pitch * -0.012 * render.rotation_sensitivity,
        )
        self.camera.lookAt(target)
        self.camera.setR(clamp(-state.roll * 0.18 * render.rotation_sensitivity, -5.0, 5.0))

        lens = self.cam.node().getLens()
        if isinstance(lens, Lens):
            fov = clamp(
                render.base_fov + state.head_z * 10.0 * render.sensitivity_z,
                render.min_fov,
                render.max_fov,
            )
            lens.setFov(fov)

    def _apply_off_axis_camera(
        self,
        state: TrackingState,
        head_x: float,
        head_y: float,
        head_z: float,
        parallax: float,
    ) -> None:
        render = self.settings.render
        eye = physical_eye_pose_units(
            head_x=head_x,
            head_y=head_y,
            head_z=head_z,
            parallax=parallax,
            settings=render,
        )
        screen_y = render.virtual_screen_y
        self.camera.setPos(eye.x, screen_y - eye.distance, eye.z)
        self.camera.setHpr(0.0, 0.0, clamp(-state.roll * 0.08 * render.rotation_sensitivity, -2.0, 2.0))

        lens = self.cam.node().getLens()
        if isinstance(lens, PerspectiveLens):
            ul_raw, ur_raw, ll_raw, lr_raw = off_axis_frustum_corners(eye)
            ul = Vec3(*ul_raw)
            ur = Vec3(*ur_raw)
            ll = Vec3(*ll_raw)
            lr = Vec3(*lr_raw)
            lens.setFrustumFromCorners(ul, ur, ll, lr, Lens.FC_off_axis | Lens.FC_aspect_ratio)
            lens.setNearFar(0.08, 75.0)

    def _amplify_head_motion(self, value: float) -> float:
        exponent = self.settings.render.off_axis_motion_exponent
        value = clamp(value, -1.4, 1.4)
        if abs(value) < 0.002:
            return 0.0
        return (1.0 if value > 0 else -1.0) * (abs(value) ** exponent)

    def _smooth_visual_tracking(
        self,
        current: TrackingState,
        target: TrackingState,
        dt: float,
    ) -> TrackingState:
        if current.timestamp == 0.0:
            return target

        rate = max(1.0, self.settings.render.visual_response_rate)
        alpha = 1.0 - exp(-dt * rate)
        deadzone = self.settings.render.visual_jitter_deadzone

        def blend(a: float, b: float) -> float:
            delta = b - a
            if abs(delta) < deadzone:
                return a
            return a + delta * alpha

        return replace(
            target,
            head_x=blend(current.head_x, target.head_x),
            head_y=blend(current.head_y, target.head_y),
            head_z=blend(current.head_z, target.head_z),
            yaw=blend(current.yaw, target.yaw),
            pitch=blend(current.pitch, target.pitch),
            roll=blend(current.roll, target.roll),
        )

    def _update_overlay(self) -> None:
        if not self.overlay.visible:
            return
        from holowindow.ui.debug_overlay import DebugSnapshot

        camera = self.runtime.camera.selected_camera
        if camera is None:
            camera_label = "none"
        else:
            camera_label = f"{camera.name} [{camera.index}] {self.runtime.camera.transform_label}"
        snapshot = DebugSnapshot(
            fps=float(self.clock.getAverageFrameRate()),
            tracking_fps=self.runtime.tracking_fps,
            frame_age_ms=self.runtime.frame_age_ms,
            inference_ms=self.runtime.inference_ms,
            camera_label=camera_label,
            scene_name=self.active_scene_name,
            calibrated=self.runtime.calibration.is_calibrated,
            smoothing=self.runtime.smoother.settings.smoothing_alpha_position,
            parallax=self.settings.render.parallax_sensitivity,
            tracking_state=self._visual_tracking,
        )
        self.overlay.update_text(snapshot, self.settings)
        self.overlay.update_preview(self._last_frame_bgr)

    def _calibrate(self) -> None:
        self.runtime.calibrate()

    def _reset_tracking(self) -> None:
        self.runtime.reset_tracking()

    def _cycle_camera(self) -> None:
        self.runtime.cycle_camera()

    def _toggle_camera_rotate(self) -> None:
        self.runtime.camera.toggle_rotate_180()
        self.runtime.reset_tracking(keep_calibration=True)

    def _toggle_camera_mirror(self) -> None:
        self.runtime.camera.toggle_flip_horizontal()
        self.runtime.reset_tracking(keep_calibration=True)

    def _toggle_camera_vertical_flip(self) -> None:
        self.runtime.camera.toggle_flip_vertical()
        self.runtime.reset_tracking(keep_calibration=True)

    def _toggle_fullscreen(self) -> None:
        props = WindowProperties()
        render_settings = self.settings.render
        render_settings.fullscreen = not render_settings.fullscreen
        props.setFullscreen(render_settings.fullscreen)
        self.win.requestProperties(props)

    def _adjust_parallax(self, delta: float) -> None:
        render = self.settings.render
        render.parallax_sensitivity = clamp(render.parallax_sensitivity + delta, 0.25, 4.0)

    def _adjust_smoothing(self, delta: float) -> None:
        self.runtime.smoother.adjust_smoothing(delta)

    def _toggle_off_axis_projection(self) -> None:
        render = self.settings.render
        render.off_axis_projection = not render.off_axis_projection
        lens = self.cam.node().getLens()
        if isinstance(lens, PerspectiveLens):
            lens.setFilmOffset(0.0, 0.0)
            lens.setFov(render.base_fov)
            lens.setNearFar(0.08, 75.0)


class HoloWindowRuntime:
    """Runtime bridge between OpenCV tracking and Panda3D rendering."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or AppSettings()
        self.debug_frame = None
        self.debug_preview_enabled = True

        from holowindow.camera.camera_manager import CameraManager
        from holowindow.tracking.calibration import CalibrationManager
        from holowindow.tracking.face_tracker import FaceTracker
        from holowindow.tracking.smoothing import TrackingSmoother

        self.camera = CameraManager(self.settings.camera)
        self.tracker = FaceTracker(self.settings.tracking)
        self.calibration = CalibrationManager(self.settings.tracking)
        self.smoother = TrackingSmoother(self.settings.tracking)
        self._last_raw = TrackingState.neutral()
        self._last_smoothed = TrackingState.neutral()
        self._last_tracking_at = 0.0
        self._last_processed_frame_timestamp = 0.0
        self._last_preview_at = 0.0
        self.tracking_fps = 0.0
        self.frame_age_ms = 0.0
        self.inference_ms = 0.0

    def start(self) -> int:
        self.camera.enumerate_devices()
        self.camera.open_first_available()
        renderer = HoloWindowRenderer(self)
        renderer.run()
        return 0

    def update_tracking(self) -> TrackingState:
        frame = self.camera.read()
        now = time.monotonic()
        if frame is None:
            if now - self._last_tracking_at < self._tracking_interval:
                return self._last_smoothed
            raw = replace(
                TrackingState.neutral(),
                tracking_lost=True,
                source_mode="unknown",
                camera_index=self.camera.current_index,
            )
            self.debug_frame = None
        else:
            self.frame_age_ms = max(0.0, (now - frame.timestamp) * 1000.0)
            if self.debug_preview_enabled and now - self._last_preview_at >= 0.1:
                self.debug_frame = self._make_debug_frame(frame.image)
                self._last_preview_at = now
            elif not self.debug_preview_enabled:
                self.debug_frame = None
            if (
                frame.timestamp == self._last_processed_frame_timestamp
                or now - self._last_tracking_at < self._tracking_interval
            ):
                return self._last_smoothed
            started_at = time.perf_counter()
            raw = self.tracker.process_frame(
                frame.image,
                timestamp=frame.timestamp,
                camera_index=frame.camera_index,
                source_mode=frame.mode,
            )
            self.inference_ms = (time.perf_counter() - started_at) * 1000.0
            self._last_processed_frame_timestamp = frame.timestamp

        self._last_raw = raw
        calibrated = self.calibration.apply(raw)
        previous_tracking_at = self._last_tracking_at
        self._last_tracking_at = now
        self.tracking_fps = self._estimate_tracking_fps(now, previous_tracking_at)
        self._last_smoothed = self.smoother.update(calibrated, now=now)
        return self._last_smoothed

    def _estimate_tracking_fps(self, now: float, previous_tracking_at: float) -> float:
        if previous_tracking_at <= 0.0:
            return self.tracking_fps
        interval = max(1e-6, now - previous_tracking_at)
        sample = min(120.0, 1.0 / interval)
        if self.tracking_fps <= 0.0:
            return sample
        return self.tracking_fps + (sample - self.tracking_fps) * 0.18

    @property
    def _tracking_interval(self) -> float:
        return 1.0 / max(1.0, self.settings.tracking.max_tracking_fps)

    def calibrate(self) -> bool:
        return self.calibration.calibrate(self._last_raw)

    def reset_tracking(self, *, keep_calibration: bool = False) -> None:
        if not keep_calibration:
            self.calibration.reset()
        self.smoother.reset()
        self._last_smoothed = TrackingState.neutral()
        self._last_tracking_at = 0.0
        self._last_processed_frame_timestamp = 0.0

    def cycle_camera(self) -> bool:
        self.debug_frame = None
        self.smoother.reset()
        return self.camera.cycle()

    def close(self) -> None:
        self.camera.release()
        self.tracker.close()

    def _make_debug_frame(self, frame):
        annotated = self.tracker.draw_debug(frame)
        height, width = annotated.shape[:2]
        if width <= 360:
            return annotated
        scale = 360.0 / width
        import cv2

        return cv2.resize(annotated, (360, int(height * scale)), interpolation=cv2.INTER_AREA)


def run_app() -> int:
    try:
        return HoloWindowRuntime().start()
    except (MissingRenderDependencyError, ModuleNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        print("Install dependencies with: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
