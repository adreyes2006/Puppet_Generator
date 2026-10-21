from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PRESET_SCHEMA_V1 = "styling-preset-v1"
PRESET_SCHEMA = "styling-preset-v2"

FILL_MODES = ("solid", "outline")

PART_NAMES = (
    "head",
    "torso",
    "upper_arm.L",
    "upper_arm.R",
    "forearm.L",
    "forearm.R",
    "hand.L",
    "hand.R",
    "thigh.L",
    "thigh.R",
    "shin.L",
    "shin.R",
    "foot.L",
    "foot.R",
)

ATTACH_BONES = ("foot.L", "foot.R", "head")

_TOP_LEVEL_KEYS = {
    "schema",
    "fill_mode",
    "materials",
    "accessories",
    "background",
    "outline",
}
_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


class PresetError(ValueError):
    pass


def validate_preset_filename(filename: str) -> None:
    if not isinstance(filename, str) or not filename:
        raise PresetError("preset filename must be a non-empty string")
    if Path(filename).name != filename or not _FILENAME.fullmatch(filename):
        raise PresetError(f"Invalid preset filename: {filename!r}")


def _validate_accessory(entry: Any) -> dict[str, str]:
    if not isinstance(entry, dict):
        raise PresetError(f"accessory entry must be an object: {entry!r}")
    unknown = set(entry) - {"style", "attach_bone"}
    if unknown:
        raise PresetError(f"unknown accessory keys: {sorted(unknown)}")
    style = entry.get("style")
    bone = entry.get("attach_bone")
    if not isinstance(style, str) or not style:
        raise PresetError(f"accessory style must be a non-empty string: {style!r}")
    if bone not in ATTACH_BONES:
        raise PresetError(f"attach_bone must be one of {ATTACH_BONES}: {bone!r}")
    return {"style": style, "attach_bone": bone}


@dataclass(frozen=True)
class StylingPreset:
    fill_mode: str = "solid"
    materials: dict[str, str] = field(default_factory=dict)
    accessories: list[dict[str, str]] = field(default_factory=list)
    background: str | None = None
    outline: Any = None

    @classmethod
    def from_dict(cls, payload: Any) -> StylingPreset:
        if not isinstance(payload, dict):
            raise PresetError("preset must be a JSON object")
        unknown = set(payload) - _TOP_LEVEL_KEYS
        if unknown:
            raise PresetError(f"unknown preset keys: {sorted(unknown)}")
        if payload.get("schema") not in (PRESET_SCHEMA_V1, PRESET_SCHEMA):
            raise PresetError(
                f"schema must be {PRESET_SCHEMA_V1!r} or {PRESET_SCHEMA!r}: "
                f"{payload.get('schema')!r}"
            )
        fill_mode = payload.get("fill_mode", "solid")
        if fill_mode not in FILL_MODES:
            raise PresetError(f"fill_mode must be one of {FILL_MODES}: {fill_mode!r}")

        raw_materials = payload.get("materials", {})
        if not isinstance(raw_materials, dict):
            raise PresetError("materials must be an object")
        materials = {}
        for part, preset_name in raw_materials.items():
            if part not in PART_NAMES:
                raise PresetError(f"invalid part name in materials: {part!r}")
            if not isinstance(preset_name, str) or not preset_name:
                raise PresetError(f"material preset must be a non-empty string: {part}")
            materials[part] = preset_name

        raw_accessories = payload.get("accessories", [])
        if not isinstance(raw_accessories, list):
            raise PresetError("accessories must be an array")
        accessories = [_validate_accessory(entry) for entry in raw_accessories]

        background = payload.get("background")
        if background is not None and not isinstance(background, str):
            raise PresetError(f"background must be a string or null: {background!r}")

        raw_outline = payload.get("outline")
        outline = None
        if raw_outline is not None:
            from puppet_pipeline.styling.outline import OutlineSpec

            try:
                outline = OutlineSpec.from_dict(raw_outline)
            except ValueError as error:
                raise PresetError(str(error)) from error

        return cls(
            fill_mode=fill_mode,
            materials=materials,
            accessories=accessories,
            background=background,
            outline=outline,
        )

    @classmethod
    def load(cls, path: Path) -> StylingPreset:
        resolved = Path(path).expanduser()
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PresetError(f"cannot load preset {resolved}: {error}") from error
        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PRESET_SCHEMA,
            "fill_mode": self.fill_mode,
            "materials": dict(self.materials),
            "accessories": [dict(entry) for entry in self.accessories],
            "background": self.background,
            "outline": self.outline.to_dict() if self.outline else None,
        }

    def serialize(self) -> bytes:
        return (
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, separators=(",", ": "))
            + "\n"
        ).encode("utf-8")

    def save(self, path: Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        validate_preset_filename(resolved.name)
        content = self.serialize()
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{resolved.name}.",
                suffix=".tmp",
                dir=resolved.parent,
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, resolved)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return resolved

    def apply(self, limb_thickness: float = 0.10):
        """Apply this preset's materials, accessories, and background; returns StylingState."""
        import bpy

        from puppet_pipeline.styling.accessories import AccessoryBuilder
        from puppet_pipeline.styling.backgrounds import BackgroundBuilder
        from puppet_pipeline.styling.manifest import StylingState
        from puppet_pipeline.styling.materials import MaterialApplier
        from puppet_pipeline.styling.scene import setup_style_collections

        setup_style_collections()
        for part, preset_name in self.materials.items():
            obj = bpy.data.objects.get(f"pup.{part}")
            if obj is None:
                raise PresetError(f"body part not found in scene: pup.{part}")
            MaterialApplier.apply(obj, preset_name)
        MaterialApplier.set_fill_mode(self.fill_mode, limb_thickness)
        accessories_state = []
        for entry in self.accessories:
            accessories_state.extend(
                AccessoryBuilder.build(
                    entry["style"], entry["attach_bone"], limb_thickness
                )
            )
        background_state = (
            BackgroundBuilder.build(self.background)
            if self.background
            else None
        )
        outline_state = None
        if self.outline is not None and self.outline.enabled:
            if self.fill_mode == "outline":
                print(
                    "Warning: fill-mode outline overrides toon outline; "
                    "skipping outline"
                )
            else:
                from puppet_pipeline.styling.outline import OutlineApplier

                OutlineApplier.apply_all(self.outline, limb_thickness)
                outline_state = self.outline.resolve(limb_thickness)
        return StylingState(
            fill_mode=self.fill_mode,
            materials=dict(self.materials),
            accessories=accessories_state,
            background=background_state,
            outline=outline_state,
        )


def reset_styling() -> None:
    """Remove all styling objects, materials, modifiers, and the PUPPET.STYLE tree."""
    import bpy

    from puppet_pipeline.common import naming
    from puppet_pipeline.styling import naming as styling_naming
    from puppet_pipeline.styling.outline import OutlineApplier

    OutlineApplier.remove_all()

    for name in naming.GEOMETRY_BINDINGS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        for modifier in [m for m in obj.modifiers if m.type == "WIREFRAME"]:
            obj.modifiers.remove(modifier)
        obj.data.materials.clear()

    for obj in [
        o for o in bpy.data.objects if o.name.startswith(("acc.", "bg."))
    ]:
        mesh = obj.data if hasattr(obj.data, "users") else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for material in [
        m for m in bpy.data.materials if m.name.startswith("mat.")
    ]:
        bpy.data.materials.remove(material)

    for collection_name in (
        styling_naming.ACCESSORY_COLLECTION_NAME,
        styling_naming.BACKGROUND_COLLECTION_NAME,
        styling_naming.STYLE_COLLECTION_NAME,
    ):
        collection = bpy.data.collections.get(collection_name)
        if collection is not None:
            bpy.data.collections.remove(collection)
