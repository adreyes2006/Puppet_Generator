from __future__ import annotations

import math
from collections.abc import Sequence

import bpy
from mathutils import Vector

from puppet_pipeline.common import naming
from puppet_pipeline.generation.parts import PartSpec

_CAP_SEGMENTS = 8
_DEPTH_RATIO = 0.2


def _capsule_outline(length: float, radius: float) -> tuple[tuple[float, float], ...]:
    effective_radius = min(radius, length / 2)
    start_center = effective_radius
    end_center = length - effective_radius
    start_cap = tuple(
        (
            start_center + effective_radius * math.cos(math.pi / 2 + math.pi * i / _CAP_SEGMENTS),
            effective_radius * math.sin(math.pi / 2 + math.pi * i / _CAP_SEGMENTS),
        )
        for i in range(_CAP_SEGMENTS + 1)
    )
    end_cap = tuple(
        (
            end_center + effective_radius * math.cos(-math.pi / 2 + math.pi * i / _CAP_SEGMENTS),
            effective_radius * math.sin(-math.pi / 2 + math.pi * i / _CAP_SEGMENTS),
        )
        for i in range(_CAP_SEGMENTS + 1)
    )
    outline = []
    for point in start_cap + end_cap:
        if not outline or not math.isclose(point[0], outline[-1][0]) or not math.isclose(
            point[1], outline[-1][1]
        ):
            outline.append(point)
    if math.isclose(outline[0][0], outline[-1][0]) and math.isclose(
        outline[0][1], outline[-1][1]
    ):
        outline.pop()
    return tuple(outline)


def _mesh_data(part: PartSpec) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    direction = Vector(part.direction).normalized()
    perpendicular = Vector((-direction.z, 0.0, direction.x)).normalized()
    origin = Vector(part.origin)
    half_depth = part.radius * _DEPTH_RATIO / 2
    outline = _capsule_outline(part.length, part.radius)

    vertices = []
    for y in (-half_depth, half_depth):
        for longitudinal, transverse in outline:
            point = origin + direction * longitudinal + perpendicular * transverse
            vertices.append((point.x, y, point.z))

    count = len(outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces.extend(
        (
            index,
            (index + 1) % count,
            count + (index + 1) % count,
            count + index,
        )
        for index in range(count)
    )
    return vertices, faces


class GeometryBuilder:
    def __init__(self, collection: bpy.types.Collection) -> None:
        self.collection = collection

    def build(self, parts: Sequence[PartSpec]) -> dict[str, bpy.types.Object]:
        objects = {}
        for part in parts:
            naming.validate_generated_name(part.name)
            existing = bpy.data.objects.get(part.name)
            if existing is not None:
                existing_data = existing.data
                bpy.data.objects.remove(existing, do_unlink=True)
                if existing_data is not None and existing_data.users == 0:
                    bpy.data.meshes.remove(existing_data)

            vertices, faces = _mesh_data(part)
            mesh = bpy.data.meshes.new(f"{part.name}.data")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            obj = bpy.data.objects.new(part.name, mesh)
            self.collection.objects.link(obj)
            objects[part.name] = obj

        return objects
