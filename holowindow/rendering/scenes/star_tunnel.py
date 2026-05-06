"""Layered cyber tunnel scene."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import attach_line, attach_uv_sphere, attach_wire_box
from holowindow.rendering.scenes.base_scene import BaseScene


class StarTunnelScene(BaseScene):
    name = "Star Tunnel"

    def __init__(self) -> None:
        super().__init__()
        self._rings: list[NodePath] = []
        self._stars: list[tuple[NodePath, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(11)
        for i in range(16):
            ring = attach_wire_box(
                root,
                name=f"tunnel-ring-{i}",
                size=(2.5 + i * 0.11, 0.08, 1.45 + i * 0.055),
                color=Vec4(0.0, 0.82, 1.0, 0.68),
                thickness=1.1,
            )
            ring.setPos(0, 0.8 + i * 0.58, 0)
            ring.setH(i * 6.0)
            self._rings.append(ring)

        for i in range(36):
            angle = i / 36.0 * math.tau
            radius_x = 2.85
            radius_z = 1.65
            start = Vec3(math.cos(angle) * radius_x, 0.5, math.sin(angle) * radius_z)
            end = Vec3(math.cos(angle) * radius_x * 0.45, 10.0, math.sin(angle) * radius_z * 0.45)
            attach_line(
                root,
                name=f"tunnel-spoke-{i}",
                points=(start, end),
                color=Vec4(0.8, 0.25, 1.0, 0.28),
                thickness=0.7,
            )

        for i in range(150):
            color = Vec4(0.65, 0.92, 1.0, random.uniform(0.42, 0.92))
            star = attach_uv_sphere(
                root,
                name=f"tunnel-star-{i}",
                radius=random.uniform(0.012, 0.04),
                color=color,
                segments=6,
                rings=4,
                emission=color,
            )
            star.setPos(
                random.uniform(-3.5, 3.5),
                random.uniform(0.7, 10.5),
                random.uniform(-2.0, 2.0),
            )
            self._stars.append((star, random.uniform(0.4, 1.4)))

    def update(self, dt: float, elapsed: float) -> None:
        for i, ring in enumerate(self._rings):
            ring.setY(ring.getY() - dt * 0.52)
            ring.setH(ring.getH() + dt * (5.0 + i * 0.14))
            if ring.getY() < 0.55:
                ring.setY(9.9)

        for star, speed in self._stars:
            star.setY(star.getY() - dt * speed)
            if star.getY() < 0.35:
                star.setY(10.8)
            scale = 1.0 + math.sin(elapsed * speed * 2.0 + star.getX()) * 0.18
            star.setScale(scale)

