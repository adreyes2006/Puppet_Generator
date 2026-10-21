from __future__ import annotations

from dataclasses import dataclass

from mathutils import Matrix, Vector

from puppet_pipeline.styling import naming as styling_naming
from puppet_pipeline.styling.materials import (
    DEFAULT_LIMB_THICKNESS,
    MaterialApplier,
)


@dataclass(frozen=True)
class PrimitiveSpec:
    kind: str
    scale: tuple[float, float, float]
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class AccessorySpec:
    name: str
    kind: str
    material: str
    attach_bones: tuple[str, ...]
    primitives: tuple[PrimitiveSpec, ...]
    sided: bool = False


def _prim(kind, scale, offset=(0.0, 0.0, 0.0)):
    return PrimitiveSpec(kind, scale, offset)


ACCESSORY_CATALOG: dict[str, AccessorySpec] = {
    "sneakers": AccessorySpec(
        name="sneakers",
        kind="shoe",
        material="red",
        attach_bones=("foot.L", "foot.R"),
        sided=True,
        primitives=(
            _prim("box", (0.55, 0.9, 0.25), (0.0, 0.0, -0.25)),
            _prim("sphere", (0.55, 0.35, 0.3), (0.0, 0.55, -0.2)),
        ),
    ),
    "boots": AccessorySpec(
        name="boots",
        kind="shoe",
        material="black",
        attach_bones=("foot.L", "foot.R"),
        sided=True,
        primitives=(
            _prim("box", (0.55, 0.9, 0.22), (0.0, 0.0, -0.22)),
            _prim("cylinder", (0.3, 0.3, 0.55), (0.0, -0.2, 0.3)),
        ),
    ),
    "loafers": AccessorySpec(
        name="loafers",
        kind="shoe",
        material="grey",
        attach_bones=("foot.L", "foot.R"),
        sided=True,
        primitives=(
            _prim("sphere", (0.55, 0.85, 0.3), (0.0, 0.0, -0.25)),
        ),
    ),
    "cap": AccessorySpec(
        name="cap",
        kind="hat",
        material="blue",
        attach_bones=("head",),
        primitives=(
            _prim("sphere", (0.8, 0.8, 0.45), (0.0, 0.0, 0.15)),
            _prim("box", (0.75, 0.5, 0.08), (0.0, 0.85, 0.15)),
        ),
    ),
    "beanie": AccessorySpec(
        name="beanie",
        kind="hat",
        material="purple",
        attach_bones=("head",),
        primitives=(
            _prim("sphere", (0.85, 0.85, 0.6), (0.0, 0.0, 0.15)),
        ),
    ),
    "fedora": AccessorySpec(
        name="fedora",
        kind="hat",
        material="grey",
        attach_bones=("head",),
        primitives=(
            _prim("cylinder", (0.6, 0.6, 0.45), (0.0, 0.0, 0.3)),
            _prim("cylinder", (0.95, 0.95, 0.05), (0.0, 0.0, 0.12)),
        ),
    ),
}


def _collection(name: str):
    import bpy

    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.data.scenes[0].collection.children.link(collection)
    return collection


def _find_rig():
    import bpy

    from puppet_pipeline.common import naming

    rig = bpy.data.objects.get(naming.ARMATURE_OBJECT_NAME)
    if rig is None or rig.type != "ARMATURE":
        raise ValueError("Puppet rig not found in scene")
    return rig


def _primitive_geometry(
    kind: str, segments: int = 16, rings: int = 8
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    import math

    if kind == "box":
        verts = [
            (sx, sy, sz)
            for sz in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
            for sx in (-1.0, 1.0)
        ]
        faces = [
            (0, 1, 3, 2),
            (4, 6, 7, 5),
            (0, 2, 6, 4),
            (1, 5, 7, 3),
            (0, 4, 5, 1),
            (2, 3, 7, 6),
        ]
        return verts, faces
    if kind == "cylinder":
        verts = []
        for zi in (-1.0, 1.0):
            verts.extend(
                (math.cos(2 * math.pi * i / segments),
                 math.sin(2 * math.pi * i / segments),
                 zi)
                for i in range(segments)
            )
        verts.extend([(0.0, 0.0, -1.0), (0.0, 0.0, 1.0)])
        bottom, top = 2 * segments, 2 * segments + 1
        faces = [
            (i, (i + 1) % segments, segments + (i + 1) % segments, segments + i)
            for i in range(segments)
        ]
        faces.extend(
            (bottom, (i + 1) % segments, i) for i in range(segments)
        )
        faces.extend(
            (top, segments + i, segments + (i + 1) % segments)
            for i in range(segments)
        )
        return verts, faces
    if kind == "sphere":
        verts = [(0.0, 0.0, -1.0)]
        for ring in range(1, rings):
            phi = math.pi * ring / rings
            z = -math.cos(phi)
            radius = math.sin(phi)
            verts.extend(
                (
                    radius * math.cos(2 * math.pi * i / segments),
                    radius * math.sin(2 * math.pi * i / segments),
                    z,
                )
                for i in range(segments)
            )
        verts.append((0.0, 0.0, 1.0))
        top_index = len(verts) - 1
        faces = [(0, 1 + i, 1 + (i + 1) % segments) for i in range(segments)]
        for ring in range(rings - 2):
            start = 1 + ring * segments
            nxt = start + segments
            faces.extend(
                (
                    start + i,
                    start + (i + 1) % segments,
                    nxt + (i + 1) % segments,
                    nxt + i,
                )
                for i in range(segments)
            )
        last = 1 + (rings - 2) * segments
        faces.extend(
            (top_index, last + (i + 1) % segments, last + i)
            for i in range(segments)
        )
        return verts, faces
    raise ValueError(f"Unsupported accessory primitive: {kind!r}")


class AccessoryBuilder:
    """Builds procedural accessory meshes and bone-parents them to the puppet rig."""

    @staticmethod
    def build(
        style: str,
        attach_bone: str | None = None,
        limb_thickness: float = DEFAULT_LIMB_THICKNESS,
    ) -> list[dict[str, str]]:
        """Create acc.* objects for `style` on `attach_bone` (or all allowed bones)."""
        import bpy

        spec = ACCESSORY_CATALOG.get(style)
        if spec is None:
            raise ValueError(f"Unknown accessory style: {style!r}")
        if attach_bone is not None and attach_bone not in spec.attach_bones:
            raise ValueError(
                f"Accessory {style!r} cannot attach to {attach_bone!r}; "
                f"allowed: {sorted(spec.attach_bones)}"
            )

        from puppet_pipeline.styling.scene import setup_style_collections

        setup_style_collections()
        rig = _find_rig()
        targets = (attach_bone,) if attach_bone else spec.attach_bones
        results = []
        for bone_name in targets:
            side = bone_name.rsplit(".", 1)[-1] if spec.sided else None
            object_name = styling_naming.accessory_name(spec.kind, spec.name, side)
            existing = bpy.data.objects.get(object_name)
            if existing is not None:
                AccessoryBuilder.remove(object_name)

            accessory = AccessoryBuilder._build_mesh(spec, limb_thickness)
            accessory.name = object_name
            accessory.data.name = object_name

            accessories_collection = _collection(
                styling_naming.ACCESSORY_COLLECTION_NAME
            )
            for user_collection in list(accessory.users_collection):
                user_collection.objects.unlink(accessory)
            accessories_collection.objects.link(accessory)

            MaterialApplier.apply(accessory, spec.material)
            AccessoryBuilder._attach(
                accessory, rig, bone_name, AccessoryBuilder._attach_target(rig, spec, bone_name)
            )
            results.append(
                {
                    "name": object_name,
                    "style": spec.name,
                    "attach_bone": bone_name,
                }
            )
        return results

    @staticmethod
    def _attach_target(rig, spec: AccessorySpec, bone_name: str) -> Vector:
        pose_bone = rig.pose.bones[bone_name]
        bone_length = rig.data.bones[bone_name].length
        head_world = rig.matrix_world @ pose_bone.matrix.translation
        tail_world = rig.matrix_world @ (
            pose_bone.matrix @ Vector((0.0, bone_length, 0.0))
        )
        if spec.kind == "hat":
            return tail_world
        return (head_world + tail_world) * 0.5

    @staticmethod
    def _attach(accessory, rig, bone_name: str, target_world: Vector) -> None:
        accessory.parent = rig
        accessory.parent_type = "BONE"
        accessory.parent_bone = bone_name
        accessory.matrix_world = Matrix.Translation(target_world)
        import bpy

        bpy.context.view_layer.update()

    @staticmethod
    def _build_mesh(spec: AccessorySpec, unit: float):
        import bpy

        verts: list[tuple[float, float, float]] = []
        faces: list[tuple[int, ...]] = []
        for prim in spec.primitives:
            base = len(verts)
            prim_verts, prim_faces = _primitive_geometry(prim.kind)
            scaled = tuple(v * unit for v in prim.scale)
            offset = tuple(v * unit for v in prim.offset)
            verts.extend(
                (
                    vx * scaled[0] + offset[0],
                    vy * scaled[1] + offset[1],
                    vz * scaled[2] + offset[2],
                )
                for vx, vy, vz in prim_verts
            )
            faces.extend(tuple(base + i for i in face) for face in prim_faces)

        mesh = bpy.data.meshes.new("acc.temp")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new("acc.temp", mesh)
        _collection(styling_naming.ACCESSORY_COLLECTION_NAME).objects.link(obj)
        return obj

    @staticmethod
    def remove(name: str) -> None:
        """Delete an accessory object and its orphaned mesh; warn-noop if absent."""
        import bpy

        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f"Warning: accessory not found: {name!r}")
            return
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
