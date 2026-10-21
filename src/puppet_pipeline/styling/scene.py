from __future__ import annotations

from dataclasses import dataclass

import bpy

from puppet_pipeline.common import naming
from puppet_pipeline.styling import naming as styling_naming


class StylingSceneError(ValueError):
    pass


@dataclass(frozen=True)
class StyleCollections:
    root: object
    accessories: object
    background: object


def validate_puppet_scene() -> list[str]:
    warnings: list[str] = []
    if naming.ARMATURE_OBJECT_NAME not in bpy.data.objects:
        raise StylingSceneError(
            f"scene has no generated puppet: missing {naming.ARMATURE_OBJECT_NAME!r}"
        )
    missing = [
        object_name
        for object_name in naming.GEOMETRY_BINDINGS
        if object_name not in bpy.data.objects
    ]
    if missing:
        raise StylingSceneError(
            f"scene has no generated puppet: missing objects {missing}"
        )
    extra = [
        obj.name
        for obj in bpy.data.objects
        if obj.name.startswith("pup.") and obj.name not in naming.GEOMETRY_BINDINGS
    ]
    if extra:
        warnings.append(
            f"non-canonical parts present, styling may be incomplete: {extra}"
        )
    stray = [
        obj.name
        for obj in bpy.data.objects
        if not obj.name.startswith(("pup.", "acc.", "bg.", "rig"))
    ]
    if stray:
        warnings.append(
            f"non-pipeline objects in scene will render in previews: {stray}"
        )
    return warnings


def _get_or_create_collection(name: str, parent) -> object:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if parent is not None and collection.name not in parent.children:
        parent.children.link(collection)
    return collection


def setup_style_collections() -> StyleCollections:
    scene_collection = bpy.context.scene.collection
    root = bpy.data.collections.get(naming.ROOT_COLLECTION_NAME)
    if root is None:
        root = bpy.data.collections.new(naming.ROOT_COLLECTION_NAME)
    if root.name not in scene_collection.children:
        scene_collection.children.link(root)

    style = _get_or_create_collection(styling_naming.STYLE_COLLECTION_NAME, root)
    accessories = _get_or_create_collection(
        styling_naming.ACCESSORY_COLLECTION_NAME, style
    )
    background = _get_or_create_collection(
        styling_naming.BACKGROUND_COLLECTION_NAME, style
    )
    return StyleCollections(root=style, accessories=accessories, background=background)
