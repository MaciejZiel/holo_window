"""Single-cube diagnostic scene for tuning head-coupled projection."""

from __future__ import annotations

import math

from panda3d.core import NodePath, Vec4

from holowindow.rendering.geometry import attach_cube, attach_panel
from holowindow.rendering.scenes.base_scene import BaseScene


class ReferenceCubeScene(BaseScene):
    name = "Reference Cube"

    def __init__(self) -> None:
        super().__init__()
        self._cube: NodePath | None = None
        self._screen_glow: NodePath | None = None

    def build(self, root: NodePath) -> None:
        attach_panel(
            root,
            name="reference-backdrop",
            width=32.0,
            height=18.0,
            y=9.0,
            color=Vec4(0.004, 0.007, 0.018, 1.0),
        )

        self._cube = attach_cube(
            root,
            name="reference-cube",
            size=1.65,
            color=Vec4(0.05, 0.82, 1.0, 0.86),
            emission=Vec4(0.0, 0.22, 0.32, 1.0),
        )
        self._cube.setPos(0.0, 4.2, 0.0)
        self._cube.setHpr(34.0, -18.0, 8.0)

    def update(self, dt: float, elapsed: float) -> None:
        if self._cube is None:
            return
        self._cube.setH(34.0 + math.sin(elapsed * 0.22) * 3.0)
        self._cube.setP(-18.0 + math.sin(elapsed * 0.17) * 2.0)
