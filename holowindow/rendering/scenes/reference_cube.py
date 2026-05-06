"""Single-cube diagnostic scene for tuning head-coupled projection."""

from __future__ import annotations

import math

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import attach_cube, attach_line, attach_panel
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
            name="reference-screen-plane",
            width=11.6,
            height=6.5,
            y=2.1,
            color=Vec4(0.04, 0.14, 0.26, 0.16),
        )
        attach_panel(
            root,
            name="reference-backdrop",
            width=13.0,
            height=7.2,
            y=8.2,
            color=Vec4(0.01, 0.018, 0.04, 1.0),
        )

        edge_color = Vec4(0.0, 0.82, 1.0, 0.38)
        for x in (-5.8, 5.8):
            attach_line(
                root,
                name=f"screen-edge-v-{x}",
                points=(Vec3(x, 2.08, -3.25), Vec3(x, 2.08, 3.25)),
                color=edge_color,
                thickness=1.2,
            )
        for z in (-3.25, 3.25):
            attach_line(
                root,
                name=f"screen-edge-h-{z}",
                points=(Vec3(-5.8, 2.08, z), Vec3(5.8, 2.08, z)),
                color=edge_color,
                thickness=1.2,
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

        attach_line(
            root,
            name="depth-line-center",
            points=(Vec3(0.0, 2.1, 0.0), Vec3(0.0, 8.0, 0.0)),
            color=Vec4(0.5, 0.9, 1.0, 0.24),
            thickness=0.8,
        )

    def update(self, dt: float, elapsed: float) -> None:
        if self._cube is None:
            return
        self._cube.setH(34.0 + math.sin(elapsed * 0.22) * 3.0)
        self._cube.setP(-18.0 + math.sin(elapsed * 0.17) * 2.0)
