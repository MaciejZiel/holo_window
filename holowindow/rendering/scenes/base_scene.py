"""Scene abstraction used by the HoloWindow renderer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from panda3d.core import NodePath


class BaseScene(ABC):
    name = "Scene"

    def __init__(self) -> None:
        self.root: NodePath | None = None

    def setup(self, parent: NodePath) -> None:
        self.root = parent.attachNewNode(self.name)
        self.build(self.root)

    @abstractmethod
    def build(self, root: NodePath) -> None:
        """Create all static scene nodes."""

    def update(self, dt: float, elapsed: float) -> None:
        """Animate the scene."""

    def destroy(self) -> None:
        if self.root is not None:
            self.root.removeNode()
        self.root = None

