"""Panda3D debug overlay for tracking and camera status."""

from __future__ import annotations

from dataclasses import dataclass

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, NodePath, TextNode, Texture

from holowindow.config.settings import AppSettings
from holowindow.tracking.tracking_state import TrackingState


@dataclass(slots=True)
class DebugSnapshot:
    fps: float
    camera_label: str
    scene_name: str
    calibrated: bool
    smoothing: float
    parallax: float
    tracking_state: TrackingState


class DebugOverlay:
    """Small diagnostic overlay that does not dominate the 3D scene."""

    def __init__(self, aspect2d: NodePath) -> None:
        self.visible = True
        self._text = OnscreenText(
            text="",
            parent=aspect2d,
            pos=(-1.31, 0.91),
            scale=0.035,
            align=TextNode.ALeft,
            fg=(0.72, 0.95, 1.0, 1.0),
            shadow=(0.0, 0.0, 0.0, 0.78),
            mayChange=True,
        )
        maker = CardMaker("camera-preview-card")
        maker.setFrame(-0.37, 0.0, -0.21, 0.0)
        self._preview = aspect2d.attachNewNode(maker.generate())
        self._preview.setPos(0.9, 0, -0.74)
        self._preview.setTransparency(True)
        self._preview.hide()
        self._texture = Texture("camera-preview")

    def toggle(self) -> bool:
        self.set_visible(not self.visible)
        return self.visible

    def set_visible(self, visible: bool) -> None:
        self.visible = visible
        if visible:
            self._text.show()
        else:
            self._text.hide()
            self._preview.hide()

    def update_text(self, snapshot: DebugSnapshot, settings: AppSettings) -> None:
        if not self.visible:
            return

        state = snapshot.tracking_state
        face = "yes" if state.face_detected else "no"
        if state.tracking_lost:
            face = "tracking lost"
        calibrated = "yes" if snapshot.calibrated else "no"
        text = (
            f"HoloWindow\n"
            f"FPS: {snapshot.fps:5.1f}\n"
            f"Camera: {snapshot.camera_label}\n"
            f"Tracking mode: {state.source_mode}\n"
            f"Face detected: {face}\n"
            f"Confidence: {state.confidence:0.2f}\n"
            f"Head: x {state.head_x:+0.2f}  y {state.head_y:+0.2f}  z {state.head_z:+0.2f}\n"
            f"Pose: yaw {state.yaw:+0.1f}  pitch {state.pitch:+0.1f}  roll {state.roll:+0.1f}\n"
            f"Smoothing: {snapshot.smoothing:0.2f}\n"
            f"Parallax: {snapshot.parallax:0.2f}\n"
            f"Scene: {snapshot.scene_name}\n"
            f"Calibrated: {calibrated}\n"
            f"Controls: C calibrate | D debug | U rotate cam | TAB camera | ESC exit"
        )
        self._text.setText(text)

    def update_preview(self, frame_bgr) -> None:
        if not self.visible or frame_bgr is None:
            self._preview.hide()
            return

        import cv2

        if frame_bgr.ndim == 2:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_GRAY2RGB)
        elif frame_bgr.shape[-1] == 1:
            rgb = cv2.cvtColor(frame_bgr[:, :, 0], cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        self._texture.setup2dTexture(width, height, Texture.TUnsignedByte, Texture.FRgb)
        self._texture.setRamImage(rgb.tobytes())
        self._preview.setTexture(self._texture, 1)
        self._preview.show()
