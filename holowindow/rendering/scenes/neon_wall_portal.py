"""Main showcase scene: a full-screen holographic wall with 3D depth."""

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


class NeonWallPortalScene(BaseScene):
    name = "Neon Wall Portal"

    def __init__(self) -> None:
        super().__init__()
        self._floaters: list[NodePath] = []
        self._particles: list[tuple[NodePath, float, float, float]] = []
        self._ribbons: list[tuple[NodePath, float, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(7)
        backdrop = make_holo_texture(
            "portal-wall-image",
            base=Vec4(0.005, 0.01, 0.04, 1.0),
            accent=Vec4(0.05, 0.95, 1.0, 1.0),
        )
        attach_panel(
            root,
            name="full-screen-wall-image",
            width=15.5,
            height=8.8,
            y=9.2,
            color=Vec4(0.55, 0.72, 1.0, 1.0),
            texture=backdrop,
        )
        attach_panel(
            root,
            name="transparent-screen-surface",
            width=11.6,
            height=6.4,
            y=2.15,
            color=Vec4(0.08, 0.42, 0.85, 0.12),
        )

        self._build_surface_image(root)
        self._build_depth_objects(root)
        self._build_particle_field(root)

    def _build_surface_image(self, root: NodePath) -> None:
        grid_color = Vec4(0.0, 0.88, 1.0, 0.22)
        y = 2.08
        for x in [i * 0.64 for i in range(-9, 10)]:
            attach_line(
                root,
                name=f"screen-vertical-{x}",
                points=(Vec3(x, y, -3.1), Vec3(x * 0.92, y, 3.1)),
                color=grid_color,
                thickness=0.48,
            )
        for z in [i * 0.42 for i in range(-7, 8)]:
            attach_line(
                root,
                name=f"screen-horizontal-{z}",
                points=(Vec3(-5.8, y, z), Vec3(5.8, y, z)),
                color=grid_color,
                thickness=0.42,
            )

        for i in range(18):
            z = -2.65 + i * 0.31
            attach_line(
                root,
                name=f"image-ribbon-{i}",
                points=(
                    Vec3(-6.2, 2.35 + i * 0.09, z),
                    Vec3(-2.2, 3.2 + i * 0.055, z + math.sin(i) * 0.24),
                    Vec3(1.4, 4.4 + i * 0.04, z - math.cos(i * 0.7) * 0.18),
                    Vec3(6.2, 6.0 + i * 0.05, z + math.sin(i * 0.4) * 0.26),
                ),
                color=Vec4(0.2, 0.7 + (i % 3) * 0.08, 1.0, 0.18),
                thickness=0.75,
            )

        for i in range(9):
            panel = attach_panel(
                root,
                name=f"floating-image-pane-{i}",
                width=1.25 + (i % 3) * 0.35,
                height=0.44 + (i % 2) * 0.22,
                y=3.15 + i * 0.52,
                x=-4.1 + i * 1.0,
                z=-2.0 + (i % 5) * 0.78,
                color=Vec4(0.0, 0.85, 1.0, 0.095),
            )
            panel.setR(-8 + i * 2.0)
            self._ribbons.append((panel, random.uniform(0.3, 0.8), random.uniform(0, math.tau)))

    def _build_depth_objects(self, root: NodePath) -> None:
        colors = (
            Vec4(0.0, 0.95, 1.0, 0.88),
            Vec4(1.0, 0.22, 0.88, 0.82),
            Vec4(0.75, 1.0, 0.25, 0.82),
            Vec4(1.0, 0.78, 0.26, 0.78),
        )

        hero = attach_octahedron(
            root,
            name="portal-hero-crystal",
            radius=0.92,
            color=Vec4(0.1, 0.95, 1.0, 0.78),
            emission=Vec4(0.0, 0.48, 0.72, 1.0),
        )
        hero.setPos(0.0, 3.45, 0.1)
        hero.setHpr(25, -18, 12)
        self._floaters.append(hero)

        for i in range(22):
            color = colors[i % len(colors)]
            if i % 4 == 0:
                node = attach_octahedron(
                    root,
                    name=f"wall-shard-{i}",
                    radius=random.uniform(0.16, 0.42),
                    color=color,
                    emission=color * 0.36,
                )
            elif i % 4 == 1:
                node = attach_cube(
                    root,
                    name=f"wall-fragment-{i}",
                    size=random.uniform(0.18, 0.45),
                    color=color,
                    emission=color * 0.28,
                )
            else:
                node = attach_uv_sphere(
                    root,
                    name=f"wall-light-node-{i}",
                    radius=random.uniform(0.075, 0.22),
                    color=color,
                    emission=color * 0.58,
                )
            node.setPos(
                random.uniform(-4.3, 4.3),
                random.uniform(2.45, 8.2),
                random.uniform(-2.25, 2.35),
            )
            if i in (3, 11, 19):
                node.setY(random.uniform(1.35, 1.85))
                node.setScale(1.15)
            node.setHpr(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
            self._floaters.append(node)

    def _build_particle_field(self, root: NodePath) -> None:
        for i in range(145):
            color = Vec4(0.25, random.uniform(0.68, 1.0), 1.0, random.uniform(0.35, 0.86))
            particle = attach_uv_sphere(
                root,
                name=f"portal-depth-particle-{i}",
                radius=random.uniform(0.012, 0.046),
                color=color,
                segments=7,
                rings=4,
                emission=color * 0.95,
            )
            depth = random.triangular(1.4, 9.0, 6.0)
            particle.setPos(
                random.uniform(-5.8, 5.8) * (0.55 + depth / 10.0),
                depth,
                random.uniform(-3.0, 3.0) * (0.55 + depth / 10.0),
            )
            self._particles.append(
                (particle, random.uniform(0.15, 0.95), random.uniform(0, math.tau), depth)
            )

    def update(self, dt: float, elapsed: float) -> None:
        for i, node in enumerate(self._floaters):
            node.setH(node.getH() + dt * (8.0 + i * 0.42))
            node.setP(node.getP() + dt * (4.5 + i * 0.26))
            node.setZ(node.getZ() + math.sin(elapsed * 0.65 + i) * dt * 0.08)

        for node, speed, phase, base_depth in self._particles:
            node.setY(base_depth + math.sin(elapsed * speed + phase) * 0.28)
            node.setX(node.getX() + math.sin(elapsed * speed * 0.7 + phase) * dt * 0.045)
            node.setZ(node.getZ() + math.cos(elapsed * speed * 0.55 + phase) * dt * 0.04)

        for node, speed, phase in self._ribbons:
            node.setColorScale(1.0, 1.0, 1.0, 0.65 + math.sin(elapsed * speed + phase) * 0.22)
            node.setZ(node.getZ() + math.sin(elapsed * speed + phase) * dt * 0.025)
