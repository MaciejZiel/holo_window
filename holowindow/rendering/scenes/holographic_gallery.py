"""Holographic object gallery embedded into the screen wall."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import (
    attach_cube,
    attach_line,
    attach_octahedron,
    attach_panel,
    attach_uv_sphere,
    make_holo_texture,
)
from holowindow.rendering.scenes.base_scene import BaseScene


class HolographicGalleryScene(BaseScene):
    name = "Holographic Wall Gallery"

    def __init__(self) -> None:
        super().__init__()
        self._cluster: NodePath | None = None
        self._orbiters: list[tuple[NodePath, float, float, float]] = []
        self._surface_layers: list[tuple[NodePath, float, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(17)
        texture = make_holo_texture(
            "gallery-wall-image",
            base=Vec4(0.008, 0.012, 0.032, 1.0),
            accent=Vec4(0.72, 0.3, 1.0, 1.0),
        )
        attach_panel(
            root,
            name="gallery-display-wall",
            width=15.4,
            height=8.7,
            y=8.8,
            color=Vec4(0.78, 0.68, 1.0, 1.0),
            texture=texture,
        )
        attach_panel(
            root,
            name="gallery-hologram-surface",
            width=11.8,
            height=6.5,
            y=2.1,
            color=Vec4(0.2, 0.62, 1.0, 0.10),
        )

        self._build_wall_composition(root)
        self._build_sculpture(root)
        self._build_orbiters(root)

    def _build_wall_composition(self, root: NodePath) -> None:
        grid_color = Vec4(0.3, 0.85, 1.0, 0.16)
        for x in [i * 0.95 for i in range(-6, 7)]:
            attach_line(
                root,
                name=f"gallery-wall-grid-x-{x}",
                points=(Vec3(x, 2.06, -3.0), Vec3(x * 0.8, 6.8, 2.7)),
                color=grid_color,
                thickness=0.48,
            )
        for i in range(7):
            z = -2.8 + i * 0.56
            attach_line(
                root,
                name=f"gallery-wall-grid-z-{i}",
                points=(Vec3(-5.8, 2.04, z), Vec3(5.8, 2.04, z)),
                color=grid_color,
                thickness=0.42,
            )

        for i in range(5):
            pane = attach_panel(
                root,
                name=f"gallery-depth-pane-{i}",
                width=random.uniform(0.72, 1.55),
                height=random.uniform(0.24, 0.72),
                y=random.uniform(2.55, 7.8),
                x=random.uniform(-4.4, 4.4),
                z=random.uniform(-2.4, 2.4),
                color=Vec4(0.65, 0.25, 1.0, random.uniform(0.04, 0.10)),
            )
            pane.setR(random.uniform(-18, 18))
            self._surface_layers.append((pane, random.uniform(0.18, 0.55), random.uniform(0, math.tau)))

    def _build_sculpture(self, root: NodePath) -> None:
        self._cluster = root.attachNewNode("wall-sculpture")
        self._cluster.setPos(0, 3.35, 0.08)
        self._cluster.setHpr(18, -4, 0)
        colors = (
            Vec4(0.0, 0.96, 1.0, 0.84),
            Vec4(0.98, 0.22, 1.0, 0.78),
            Vec4(0.78, 1.0, 0.34, 0.78),
            Vec4(1.0, 0.62, 0.24, 0.74),
        )

        core = attach_octahedron(
            self._cluster,
            name="gallery-core-crystal",
            radius=0.84,
            color=Vec4(0.08, 0.95, 1.0, 0.72),
            emission=Vec4(0.0, 0.55, 0.8, 1.0),
        )
        core.setHpr(0, 12, 16)

        for i in range(9):
            color = colors[i % len(colors)]
            if i % 2 == 0:
                node = attach_octahedron(
                    self._cluster,
                    name=f"sculpture-shard-{i}",
                    radius=0.22 + (i % 5) * 0.05,
                    color=color,
                    emission=color * 0.34,
                )
            else:
                node = attach_cube(
                    self._cluster,
                    name=f"sculpture-block-{i}",
                    size=0.25 + (i % 4) * 0.055,
                    color=color,
                    emission=color * 0.24,
                )
            angle = i / 9.0 * math.tau
            radius = 0.62 + (i % 4) * 0.22
            node.setPos(
                math.cos(angle) * radius,
                math.sin(angle * 1.7) * 0.36,
                math.sin(angle) * radius * 0.56,
            )
            node.setHpr(i * 31, 25 + i * 7, i * 17)

    def _build_orbiters(self, root: NodePath) -> None:
        for i in range(34):
            color = Vec4(
                random.uniform(0.15, 0.65),
                random.uniform(0.62, 1.0),
                1.0,
                random.uniform(0.35, 0.86),
            )
            node = attach_uv_sphere(
                root,
                name=f"gallery-depth-orbiter-{i}",
                radius=random.uniform(0.018, 0.07),
                color=color,
                segments=8,
                rings=5,
                emission=color,
            )
            self._orbiters.append(
                (
                    node,
                    random.uniform(0.75, 3.3),
                    random.uniform(0.26, 1.05),
                    random.uniform(0, math.tau),
                )
            )

    def update(self, dt: float, elapsed: float) -> None:
        if self._cluster is not None:
            self._cluster.setH(self._cluster.getH() + dt * 9.0)
            self._cluster.setP(math.sin(elapsed * 0.45) * 4.5)

        for node, radius, speed, phase in self._orbiters:
            angle = elapsed * speed + phase
            depth_offset = math.sin(angle * 0.52 + phase) * 1.15
            node.setPos(
                math.cos(angle) * radius,
                3.55 + depth_offset,
                math.sin(angle) * radius * 0.56,
            )

        for pane, speed, phase in self._surface_layers:
            pane.setX(pane.getX() + math.sin(elapsed * speed + phase) * dt * 0.04)
            pane.setColorScale(1.0, 1.0, 1.0, 0.7 + math.sin(elapsed * speed * 1.7 + phase) * 0.18)
