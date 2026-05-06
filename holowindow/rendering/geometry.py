"""Procedural geometry helpers for Panda3D scenes."""

from __future__ import annotations

import math
from typing import Iterable

from panda3d.core import (
    CardMaker,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    Material,
    NodePath,
    PNMImage,
    Texture,
    TransparencyAttrib,
    Vec3,
    Vec4,
)


def make_material(
    color: Vec4,
    *,
    emission: Vec4 | None = None,
    shininess: float = 48.0,
) -> Material:
    material = Material()
    material.setDiffuse(color)
    material.setAmbient(color * 0.55)
    material.setSpecular(Vec4(0.9, 0.95, 1.0, 1.0))
    material.setShininess(shininess)
    if emission is not None:
        material.setEmission(emission)
    return material


def attach_line(
    parent: NodePath,
    *,
    name: str,
    points: Iterable[Vec3],
    color: Vec4,
    thickness: float = 1.0,
) -> NodePath:
    lines = LineSegs(name)
    lines.setThickness(thickness)
    lines.setColor(color)
    iterator = iter(points)
    try:
        first = next(iterator)
    except StopIteration:
        return NodePath(name)
    lines.moveTo(first)
    for point in iterator:
        lines.drawTo(point)
    node = parent.attachNewNode(lines.create())
    node.setTransparency(TransparencyAttrib.MAlpha)
    return node


def make_holo_texture(
    name: str,
    *,
    width: int = 512,
    height: int = 288,
    base: Vec4 = Vec4(0.01, 0.018, 0.055, 1.0),
    accent: Vec4 = Vec4(0.0, 0.85, 1.0, 1.0),
) -> Texture:
    """Create a procedural 2D wall image used as the holographic display surface."""
    image = PNMImage(width, height, 4)
    for y in range(height):
        v = y / max(1, height - 1)
        scanline = 0.035 if y % 5 == 0 else 0.0
        for x in range(width):
            u = x / max(1, width - 1)
            center_falloff = max(0.0, 1.0 - ((u - 0.5) ** 2 * 3.8 + (v - 0.5) ** 2 * 3.2))
            wave = (math.sin(u * 33.0 + v * 9.0) + math.sin((u + v) * 19.0)) * 0.032
            grid = 0.075 if x % 64 == 0 or y % 48 == 0 else 0.0
            pulse = max(0.0, math.sin((u * 2.0 - v * 1.3) * math.tau)) * 0.045
            glow = center_falloff * 0.22 + wave + grid + scanline + pulse
            r = min(1.0, base.x + accent.x * glow + 0.02 * center_falloff)
            g = min(1.0, base.y + accent.y * glow + 0.08 * center_falloff)
            b = min(1.0, base.z + accent.z * glow + 0.18 * center_falloff)
            image.setXelA(x, y, r, g, b, 1.0)

    texture = Texture(name)
    texture.load(image)
    return texture


def attach_panel(
    parent: NodePath,
    *,
    name: str,
    width: float,
    height: float,
    y: float,
    color: Vec4,
    texture: Texture | None = None,
    x: float = 0.0,
    z: float = 0.0,
    unlit: bool = True,
) -> NodePath:
    maker = CardMaker(name)
    maker.setFrame(-width / 2.0, width / 2.0, -height / 2.0, height / 2.0)
    node = parent.attachNewNode(maker.generate())
    node.setPos(x, y, z)
    node.setColor(color)
    node.setTwoSided(True)
    if texture is not None:
        node.setTexture(texture, 1)
    if color.w < 1.0:
        node.setTransparency(TransparencyAttrib.MAlpha)
    if unlit:
        node.setLightOff(1)
    return node


def attach_cube(
    parent: NodePath,
    *,
    name: str,
    size: float,
    color: Vec4,
    emission: Vec4 | None = None,
) -> NodePath:
    half = size / 2.0
    vertices = [
        (-half, -half, -half),
        (half, -half, -half),
        (half, half, -half),
        (-half, half, -half),
        (-half, -half, half),
        (half, -half, half),
        (half, half, half),
        (-half, half, half),
    ]
    faces = [
        (0, 1, 2, 3, (0, 0, -1)),
        (4, 7, 6, 5, (0, 0, 1)),
        (0, 4, 5, 1, (0, -1, 0)),
        (1, 5, 6, 2, (1, 0, 0)),
        (2, 6, 7, 3, (0, 1, 0)),
        (3, 7, 4, 0, (-1, 0, 0)),
    ]
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(vertex_data, "vertex")
    normal = GeomVertexWriter(vertex_data, "normal")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)

    row = 0
    for a, b, c, d, face_normal in faces:
        for index in (a, b, c, d):
            vertex.addData3f(*vertices[index])
            normal.addData3f(*face_normal)
            color_writer.addData4f(color)
        triangles.addVertices(row, row + 1, row + 2)
        triangles.addVertices(row, row + 2, row + 3)
        row += 4

    geom = Geom(vertex_data)
    geom.addPrimitive(triangles)
    geom_node = GeomNode(name)
    geom_node.addGeom(geom)
    node = parent.attachNewNode(geom_node)
    node.setMaterial(make_material(color, emission=emission), 1)
    if color.w < 1.0:
        node.setTransparency(TransparencyAttrib.MAlpha)
    return node


def attach_octahedron(
    parent: NodePath,
    *,
    name: str,
    radius: float,
    color: Vec4,
    emission: Vec4 | None = None,
) -> NodePath:
    vertices = [
        Vec3(0, 0, radius),
        Vec3(radius, 0, 0),
        Vec3(0, radius, 0),
        Vec3(-radius, 0, 0),
        Vec3(0, -radius, 0),
        Vec3(0, 0, -radius),
    ]
    faces = (
        (0, 1, 2),
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 1),
        (5, 2, 1),
        (5, 3, 2),
        (5, 4, 3),
        (5, 1, 4),
    )
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(vertex_data, "vertex")
    normal = GeomVertexWriter(vertex_data, "normal")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)

    row = 0
    for a, b, c in faces:
        face_normal = (vertices[b] - vertices[a]).cross(vertices[c] - vertices[a])
        face_normal.normalize()
        for index in (a, b, c):
            vertex.addData3f(vertices[index])
            normal.addData3f(face_normal)
            color_writer.addData4f(color)
        triangles.addVertices(row, row + 1, row + 2)
        row += 3

    geom = Geom(vertex_data)
    geom.addPrimitive(triangles)
    geom_node = GeomNode(name)
    geom_node.addGeom(geom)
    node = parent.attachNewNode(geom_node)
    node.setMaterial(make_material(color, emission=emission), 1)
    if color.w < 1.0:
        node.setTransparency(TransparencyAttrib.MAlpha)
    return node


def attach_uv_sphere(
    parent: NodePath,
    *,
    name: str,
    radius: float,
    color: Vec4,
    segments: int = 18,
    rings: int = 10,
    emission: Vec4 | None = None,
) -> NodePath:
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(vertex_data, "vertex")
    normal = GeomVertexWriter(vertex_data, "normal")
    color_writer = GeomVertexWriter(vertex_data, "color")

    for ring in range(rings + 1):
        v = ring / rings
        theta = v * math.pi
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        for segment in range(segments + 1):
            u = segment / segments
            phi = u * math.tau
            x = math.cos(phi) * sin_theta
            y = math.sin(phi) * sin_theta
            z = cos_theta
            vertex.addData3f(x * radius, y * radius, z * radius)
            normal.addData3f(x, y, z)
            color_writer.addData4f(color)

    triangles = GeomTriangles(Geom.UHStatic)
    for ring in range(rings):
        for segment in range(segments):
            current = ring * (segments + 1) + segment
            next_row = current + segments + 1
            triangles.addVertices(current, next_row, current + 1)
            triangles.addVertices(current + 1, next_row, next_row + 1)

    geom = Geom(vertex_data)
    geom.addPrimitive(triangles)
    geom_node = GeomNode(name)
    geom_node.addGeom(geom)
    node = parent.attachNewNode(geom_node)
    node.setMaterial(make_material(color, emission=emission), 1)
    if color.w < 1.0:
        node.setTransparency(TransparencyAttrib.MAlpha)
    return node
