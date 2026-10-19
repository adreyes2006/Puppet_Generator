from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from puppet_pipeline.common import naming


class BindingApplier:
    @staticmethod
    def bind(objects: Mapping[str, Any], armature: Any) -> None:
        from mathutils import Matrix

        missing = set(naming.GEOMETRY_BINDINGS) - set(objects)
        if missing:
            raise ValueError(
                f"Cannot bind puppet; missing geometry objects: {sorted(missing)}"
            )

        armature_bones = {bone.name for bone in armature.data.bones}
        required_bones = set(naming.GEOMETRY_BINDINGS.values())
        if missing_bones := required_bones - armature_bones:
            raise ValueError(
                f"Cannot bind puppet; missing deform bones: {sorted(missing_bones)}"
            )

        for object_name, bone_name in naming.GEOMETRY_BINDINGS.items():
            obj = objects[object_name]
            if obj.type != "MESH":
                raise ValueError(f"Cannot bind non-mesh object: {object_name}")

            for vertex_group in list(obj.vertex_groups):
                obj.vertex_groups.remove(vertex_group)
            vertex_group = obj.vertex_groups.new(name=bone_name)
            vertex_group.add(
                [vertex.index for vertex in obj.data.vertices],
                1.0,
                "REPLACE",
            )

            for modifier in list(obj.modifiers):
                if modifier.type == "ARMATURE":
                    obj.modifiers.remove(modifier)
            modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
            modifier.object = armature

            obj.parent = armature
            obj.parent_type = "OBJECT"
            obj.matrix_parent_inverse = Matrix.Identity(4)
