from __future__ import annotations

import re
from dataclasses import dataclass

import bpy

from puppet_pipeline.common import naming

_NUMERIC_DUPLICATE = re.compile(r"\.\d{3}$")


@dataclass(frozen=True)
class PuppetCollections:
    root: bpy.types.Collection
    geometry: bpy.types.Collection
    rig: bpy.types.Collection


def _is_named_duplicate(name: str, contract_name: str) -> bool:
    if name == contract_name:
        return True
    suffix = name.removeprefix(contract_name)
    return name.startswith(contract_name) and _NUMERIC_DUPLICATE.fullmatch(suffix) is not None


def _is_generated_collection(name: str) -> bool:
    return any(
        _is_named_duplicate(name, contract_name)
        for contract_name in (
            naming.ROOT_COLLECTION_NAME,
            naming.GEOMETRY_COLLECTION_NAME,
            naming.RIG_COLLECTION_NAME,
        )
    )


def _remove_generated_objects() -> None:
    generated_objects = [
        obj
        for obj in bpy.data.objects
        if obj.name.startswith("pup.") or obj.name == naming.ARMATURE_OBJECT_NAME
    ]
    object_data = [(obj.type, obj.data) for obj in generated_objects if obj.data]

    for obj in generated_objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    for object_type, data in object_data:
        if data.users != 0:
            continue
        if object_type == "MESH" and data.name in bpy.data.meshes:
            bpy.data.meshes.remove(data)
        elif object_type == "ARMATURE" and data.name in bpy.data.armatures:
            bpy.data.armatures.remove(data)

    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("pup.") and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for armature in list(bpy.data.armatures):
        if armature.name == naming.ARMATURE_DATA_NAME and armature.users == 0:
            bpy.data.armatures.remove(armature)


def _remove_generated_collections() -> None:
    generated_collections = sorted(
        (
            collection
            for collection in bpy.data.collections
            if _is_generated_collection(collection.name)
        ),
        key=lambda collection: len(collection.name),
        reverse=True,
    )
    for collection in generated_collections:
        bpy.data.collections.remove(collection)


def reset_puppet_scene() -> PuppetCollections:
    _remove_generated_objects()
    _remove_generated_collections()

    root = bpy.data.collections.new(naming.ROOT_COLLECTION_NAME)
    geometry = bpy.data.collections.new(naming.GEOMETRY_COLLECTION_NAME)
    rig = bpy.data.collections.new(naming.RIG_COLLECTION_NAME)

    bpy.context.scene.collection.children.link(root)
    root.children.link(geometry)
    root.children.link(rig)

    return PuppetCollections(root=root, geometry=geometry, rig=rig)
