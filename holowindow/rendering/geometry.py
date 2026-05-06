"""Procedural geometry helpers for Panda3D scenes."""

from __future__ import annotations

import math
from typing import Iterable

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    Material,
    NodePath,
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


def attach_wire_box(
    parent: NodePath,
    *,
    name: str,
    size: tuple[float, float, float],
    color: Vec4,
    thickness: float = 1.6,
) -> NodePath:
    sx, sy, sz = (axis / 2.0 for axis in size)
    corners = [
        Vec3(-sx, -sy, -sz),
        Vec3(sx, -sy, -sz),
        Vec3(sx, sy, -sz),
        Vec3(-sx, sy, -sz),
        Vec3(-sx, -sy, sz),
        Vec3(sx, -sy, sz),
        Vec3(sx, sy, sz),
        Vec3(-sx, sy, sz),
    ]
    edges = (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    )
    lines = LineSegs(name)
    lines.setThickness(thickness)
    lines.setColor(color)
    for a, b in edges:
        lines.moveTo(corners[a])
        lines.drawTo(corners[b])
    node = parent.attachNewNode(lines.create())
    node.setTransparency(TransparencyAttrib.MAlpha)
    return node


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

