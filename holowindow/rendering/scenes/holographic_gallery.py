"""Holographic object gallery scene."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import attach_cube, attach_line, attach_uv_sphere, attach_wire_box
from holowindow.rendering.scenes.base_scene import BaseScene


class HolographicGalleryScene(BaseScene):
    name = "Holographic Gallery"

    def __init__(self) -> None:
        super().__init__()
        self._cluster: NodePath | None = None
        self._orbiters: list[tuple[NodePath, float, float, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(17)
        attach_wire_box(
            root,
            name="gallery-frame",
            size=(4.6, 5.8, 2.8),
            color=Vec4(0.2, 1.0, 0.88, 0.5),
            thickness=1.3,
        ).setPos(0, 4.2, 0)

        grid_color = Vec4(0.25, 0.75, 1.0, 0.24)
        for x in [i * 0.55 for i in range(-5, 6)]:
            attach_line(
                root,
                name=f"gallery-grid-x-{x}",
                points=(Vec3(x, 1.0, -1.35), Vec3(x * 0.45, 7.5, -0.9)),
                color=grid_color,
                thickness=0.65,
            )
        for i in range(6):
            z = -1.35 + i * 0.45
            attach_line(
                root,
                name=f"gallery-grid-z-{i}",
                points=(Vec3(-2.6, 1.0 + i * 0.95, z), Vec3(2.6, 1.0 + i * 0.95, z)),
                color=grid_color,
                thickness=0.65,
            )

        self._cluster = root.attachNewNode("crystal-cluster")
        self._cluster.setPos(0, 4.0, 0.1)
        self._cluster.setHpr(18, 0, 0)
        colors = (
            Vec4(0.0, 0.95, 1.0, 0.82),
            Vec4(0.95, 0.18, 1.0, 0.76),
            Vec4(0.8, 1.0, 0.28, 0.76),
        )
        for i in range(9):
            node = attach_cube(
                self._cluster,
                name=f"crystal-block-{i}",
                size=0.62 - i * 0.025,
                color=colors[i % len(colors)],
                emission=colors[i % len(colors)] * 0.38,
            )
            angle = i / 9.0 * math.tau
            radius = 0.25 + (i % 4) * 0.18
            node.setPos(math.cos(angle) * radius, math.sin(angle) * radius * 0.3, math.sin(angle) * 0.55)
            node.setHpr(i * 31, 25 + i * 7, i * 17)

        for i in range(44):
            color = Vec4(0.0, random.uniform(0.65, 1.0), 1.0, random.uniform(0.35, 0.85))
            node = attach_uv_sphere(
                root,
                name=f"gallery-orbiter-{i}",
                radius=random.uniform(0.025, 0.065),
                color=color,
                segments=8,
                rings=5,
                emission=color,
            )
            self._orbiters.append(
                (
                    node,
                    random.uniform(0.9, 2.4),
                    random.uniform(0.35, 1.1),
                    random.uniform(0, math.tau),
                )
            )

    def update(self, dt: float, elapsed: float) -> None:
        if self._cluster is not None:
            self._cluster.setH(self._cluster.getH() + dt * 11.0)
            self._cluster.setP(math.sin(elapsed * 0.5) * 5.0)

        for node, radius, speed, phase in self._orbiters:
            angle = elapsed * speed + phase
            node.setPos(
                math.cos(angle) * radius,
                4.0 + math.sin(angle * 0.55 + phase) * 0.7,
                math.sin(angle) * radius * 0.48,
            )

