"""Immersive cyber tunnel rendered as a wall image with real 3D depth."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, Vec3, Vec4

from holowindow.rendering.geometry import attach_line, attach_panel, attach_uv_sphere, make_holo_texture
from holowindow.rendering.scenes.base_scene import BaseScene


class StarTunnelScene(BaseScene):
    name = "Star Wall Tunnel"

    def __init__(self) -> None:
        super().__init__()
        self._stars: list[tuple[NodePath, float, float, float]] = []
        self._streaks: list[tuple[NodePath, float, float]] = []
        self._panes: list[tuple[NodePath, float, float]] = []

    def build(self, root: NodePath) -> None:
        random.seed(11)
        texture = make_holo_texture(
            "star-wall-image",
            base=Vec4(0.002, 0.004, 0.025, 1.0),
            accent=Vec4(0.22, 0.72, 1.0, 1.0),
        )
        attach_panel(
            root,
            name="starfield-wall",
            width=16.0,
            height=9.0,
            y=10.2,
            color=Vec4(0.68, 0.78, 1.0, 1.0),
            texture=texture,
        )
        attach_panel(
            root,
            name="warp-glass-surface",
            width=12.4,
            height=6.8,
            y=2.0,
            color=Vec4(0.05, 0.2, 0.75, 0.10),
        )

        self._build_warp_lines(root)
        self._build_depth_stars(root)
        self._build_image_layers(root)

    def _build_warp_lines(self, root: NodePath) -> None:
        for i in range(34):
            angle = i / 34.0 * math.tau
            near_radius = random.uniform(0.18, 0.75)
            far_radius = random.uniform(4.2, 7.4)
            z_scale = 0.56
            start = Vec3(math.cos(angle) * near_radius, random.uniform(2.1, 3.0), math.sin(angle) * near_radius * z_scale)
            mid = Vec3(math.cos(angle) * far_radius * 0.55, random.uniform(4.0, 6.3), math.sin(angle) * far_radius * z_scale * 0.55)
            end = Vec3(math.cos(angle) * far_radius, random.uniform(7.0, 10.2), math.sin(angle) * far_radius * z_scale)
            color = Vec4(0.25 + random.random() * 0.45, 0.55 + random.random() * 0.35, 1.0, 0.18)
            line = attach_line(
                root,
                name=f"warp-streak-{i}",
                points=(start, mid, end),
                color=color,
                thickness=random.uniform(0.45, 1.1),
            )
            self._streaks.append((line, random.uniform(0.25, 0.75), random.uniform(0, math.tau)))

    def _build_depth_stars(self, root: NodePath) -> None:
        for i in range(76):
            depth = random.triangular(1.3, 10.4, 7.4)
            color = Vec4(
                random.uniform(0.55, 0.9),
                random.uniform(0.76, 1.0),
                1.0,
                random.uniform(0.42, 0.95),
            )
            star = attach_uv_sphere(
                root,
                name=f"wall-star-{i}",
                radius=random.uniform(0.01, 0.048) * (0.8 + depth * 0.05),
                color=color,
                segments=6,
                rings=4,
                emission=color,
            )
            spread = 0.52 + depth / 8.2
            star.setPos(
                random.uniform(-5.8, 5.8) * spread,
                depth,
                random.uniform(-3.1, 3.1) * spread,
            )
            self._stars.append((star, random.uniform(0.55, 1.85), random.uniform(0, math.tau), depth))

    def _build_image_layers(self, root: NodePath) -> None:
        for i in range(5):
            pane = attach_panel(
                root,
                name=f"warp-image-layer-{i}",
                width=4.4 + i * 0.9,
                height=2.4 + i * 0.45,
                y=2.55 + i * 0.74,
                color=Vec4(0.0, 0.78, 1.0, 0.045 + i * 0.006),
            )
            pane.setR(i * 7.0)
            self._panes.append((pane, random.uniform(0.12, 0.32), random.uniform(0, math.tau)))

    def update(self, dt: float, elapsed: float) -> None:
        for star, speed, phase, base_depth in self._stars:
            y = star.getY() - dt * speed * 0.85
            if y < 1.0:
                y = 10.6
            star.setY(y)
            star.setScale(1.0 + math.sin(elapsed * speed * 2.0 + phase) * 0.22)

        for line, speed, phase in self._streaks:
            line.setColorScale(1.0, 1.0, 1.0, 0.62 + math.sin(elapsed * speed + phase) * 0.34)
            line.setH(math.sin(elapsed * speed * 0.25 + phase) * 1.4)

        for pane, speed, phase in self._panes:
            pane.setR(pane.getR() + dt * speed * 9.0)
            pane.setColorScale(1.0, 1.0, 1.0, 0.72 + math.sin(elapsed * speed + phase) * 0.2)
