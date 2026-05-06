"""Main showcase scene: a glowing layered box behind the screen."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import attach_cube, attach_line, attach_uv_sphere, attach_wire_box
from holowindow.rendering.scenes.base_scene import BaseScene


class NeonDepthBoxScene(BaseScene):
    name = "Neon Depth Box"

    def __init__(self) -> None:
        super().__init__()
        self._floaters: list[NodePath] = []
        self._particles: list[tuple[NodePath, float, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(7)
        attach_wire_box(
            root,
            name="window-volume",
            size=(5.6, 8.8, 3.2),
            color=Vec4(0.0, 0.95, 1.0, 0.78),
            thickness=2.2,
        ).setPos(0, 4.2, 0)

        for i, depth in enumerate((1.4, 2.7, 4.1, 5.6, 7.1)):
            alpha = 0.72 - i * 0.08
            attach_wire_box(
                root,
                name=f"depth-slice-{i}",
                size=(5.3 - i * 0.22, 0.06, 3.0 - i * 0.12),
                color=Vec4(0.35, 0.2 + i * 0.12, 1.0, alpha),
                thickness=1.2,
            ).setPos(0, depth, 0)

        for x in (-2.7, -1.35, 0.0, 1.35, 2.7):
            attach_line(
                root,
                name=f"floor-ray-{x}",
                points=(Vec3(x, 0.4, -1.65), Vec3(x * 0.45, 8.6, -1.2)),
                color=Vec4(0.1, 0.55, 1.0, 0.35),
                thickness=0.8,
            )
        for z in (-1.45, 0.0, 1.45):
            attach_line(
                root,
                name=f"side-ray-{z}",
                points=(Vec3(-2.9, 0.6, z), Vec3(-1.2, 8.5, z * 0.72)),
                color=Vec4(0.95, 0.2, 0.95, 0.28),
                thickness=0.8,
            )
            attach_line(
                root,
                name=f"side-ray-r-{z}",
                points=(Vec3(2.9, 0.6, z), Vec3(1.2, 8.5, z * 0.72)),
                color=Vec4(0.95, 0.2, 0.95, 0.28),
                thickness=0.8,
            )

        colors = (
            Vec4(0.0, 0.9, 1.0, 0.85),
            Vec4(1.0, 0.18, 0.85, 0.8),
            Vec4(0.55, 1.0, 0.18, 0.78),
            Vec4(1.0, 0.75, 0.2, 0.8),
        )
        for i in range(18):
            color = colors[i % len(colors)]
            if i % 3 == 0:
                node = attach_cube(
                    root,
                    name=f"floating-cube-{i}",
                    size=random.uniform(0.18, 0.45),
                    color=color,
                    emission=color * 0.42,
                )
            else:
                node = attach_uv_sphere(
                    root,
                    name=f"floating-orb-{i}",
                    radius=random.uniform(0.08, 0.22),
                    color=color,
                    emission=color * 0.55,
                )
            node.setPos(
                random.uniform(-2.25, 2.25),
                random.uniform(1.0, 8.0),
                random.uniform(-1.25, 1.35),
            )
            node.setHpr(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
            self._floaters.append(node)

        for i in range(80):
            color = Vec4(0.35, random.uniform(0.65, 1.0), 1.0, random.uniform(0.35, 0.8))
            particle = attach_uv_sphere(
                root,
                name=f"depth-particle-{i}",
                radius=random.uniform(0.018, 0.045),
                color=color,
                segments=8,
                rings=5,
                emission=color * 0.8,
            )
            phase = random.uniform(0, math.tau)
            speed = random.uniform(0.35, 0.95)
            particle.setPos(
                random.uniform(-2.65, 2.65),
                random.uniform(0.6, 8.6),
                random.uniform(-1.55, 1.55),
            )
            self._particles.append((particle, phase, speed))

    def update(self, dt: float, elapsed: float) -> None:
        for i, node in enumerate(self._floaters):
            node.setH(node.getH() + dt * (10.0 + i * 0.55))
            node.setP(node.getP() + dt * (7.0 + i * 0.35))
            base_z = node.getZ()
            node.setZ(base_z + math.sin(elapsed * 0.75 + i) * dt * 0.12)

        for node, phase, speed in self._particles:
            x = node.getX() + math.sin(elapsed * speed + phase) * dt * 0.05
            z = node.getZ() + math.cos(elapsed * speed * 0.7 + phase) * dt * 0.04
            node.setX(x)
            node.setZ(z)

