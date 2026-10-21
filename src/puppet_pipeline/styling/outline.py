from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

DEFAULT_OUTLINE_COLOR = "#0d0d0d"
THICKNESS_FACTOR = 0.15
OUTLINE_MODIFIER_NAME = "outline_toon"
OUTLINE_MATERIAL_NAME = "mat.outline"

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class OutlineSpec:
    """Toon outline configuration; None fields derive at apply time."""

    enabled: bool = False
    thickness: float | None = None
    color: str | None = None

    def resolve(self, limb_thickness: float) -> dict[str, Any]:
        """Return concrete {thickness, color}; thickness defaults to limb_thickness × 0.15."""
        thickness = self.thickness
        if thickness is None:
            thickness = limb_thickness * THICKNESS_FACTOR
        elif thickness <= 0 or thickness != thickness:
            raise ValueError(
                f"outline thickness must be finite and > 0: {thickness!r}"
            )
        color = self.color or DEFAULT_OUTLINE_COLOR
        return {"enabled": self.enabled, "thickness": thickness, "color": color}

    @classmethod
    def from_dict(cls, payload: Any) -> "OutlineSpec | None":
        """Deserialize a preset/manifest outline object; None stays None."""
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise ValueError(f"outline must be an object or null: {payload!r}")
        unknown = set(payload) - {"enabled", "thickness", "color"}
        if unknown:
            raise ValueError(f"unknown outline keys: {sorted(unknown)}")
        enabled = payload.get("enabled")
        if not isinstance(enabled, bool):
            raise ValueError(f"outline.enabled must be a boolean: {enabled!r}")
        thickness = payload.get("thickness")
        if thickness is not None:
            if not isinstance(thickness, (int, float)) or thickness <= 0:
                raise ValueError(
                    f"outline.thickness must be a positive number or null: {thickness!r}"
                )
            thickness = float(thickness)
        color = payload.get("color")
        if color is not None:
            color = parse_outline_color(color)
        return cls(enabled=enabled, thickness=thickness, color=color)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "thickness": self.thickness,
            "color": self.color,
        }


def _rgba_to_hex(rgba) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        *(round(channel * 255) for channel in rgba[:3])
    )


def parse_outline_color(value: str) -> str:
    """Normalize a catalog preset name or #rrggbb string to lowercase hex."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"outline color must be a name or #rrggbb: {value!r}")
    if _HEX.fullmatch(value):
        return value.lower()
    from puppet_pipeline.styling.materials import MATERIAL_CATALOG

    preset = MATERIAL_CATALOG.get(value)
    if preset is not None:
        return _rgba_to_hex(preset.base_color)
    raise ValueError(
        f"Unknown outline color: {value!r}; expected a catalog preset name or #rrggbb"
    )


def _hex_to_rgba(hex_color: str):
    return (
        int(hex_color[1:3], 16) / 255.0,
        int(hex_color[3:5], 16) / 255.0,
        int(hex_color[5:7], 16) / 255.0,
        1.0,
    )


class OutlineApplier:
    """Applies/removes inverted-hull toon outlines on pup.* and acc.* objects."""

    @staticmethod
    def _outline_material(hex_color: str):
        import bpy

        material = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
        if material is None:
            material = bpy.data.materials.new(OUTLINE_MATERIAL_NAME)
        rgba = _hex_to_rgba(hex_color)
        material.use_nodes = True
        principled = next(
            node
            for node in material.node_tree.nodes
            if node.type == "BSDF_PRINCIPLED"
        )
        principled.inputs["Base Color"].default_value = rgba
        principled.inputs["Roughness"].default_value = 1.0
        emission = principled.inputs.get("Emission Color") or principled.inputs.get(
            "Emission"
        )
        if emission is not None:
            emission.default_value = rgba
        strength = principled.inputs.get("Emission Strength")
        if strength is not None:
            strength.default_value = 1.0
        material.diffuse_color = rgba
        return material

    @staticmethod
    def apply(obj, spec: OutlineSpec, limb_thickness: float = 0.06) -> None:
        """Add (or skip) the outline_toon Solidify modifier + mat.outline slot."""
        if not spec.enabled:
            return
        resolved = spec.resolve(limb_thickness)
        if any(m.name == OUTLINE_MODIFIER_NAME for m in obj.modifiers):
            return
        material = OutlineApplier._outline_material(resolved["color"])
        obj.data.materials.append(material)
        slot_index = len(obj.data.materials) - 1
        modifier = obj.modifiers.new(name=OUTLINE_MODIFIER_NAME, type="SOLIDIFY")
        modifier.thickness = resolved["thickness"]
        modifier.offset = -1.0
        modifier.use_flip_normals = True
        modifier.use_even_offset = True
        modifier.material_offset = slot_index

    @staticmethod
    def apply_all(spec: OutlineSpec, limb_thickness: float) -> None:
        """Apply the outline to every pup.* and acc.* object in the scene."""
        import bpy

        from puppet_pipeline.common import naming

        if not spec.enabled:
            return
        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects.get(object_name)
            if obj is not None:
                OutlineApplier.apply(obj, spec, limb_thickness)
        for obj in bpy.data.objects:
            if obj.name.startswith("acc."):
                OutlineApplier.apply(obj, spec, limb_thickness)

    @staticmethod
    def remove_from(obj) -> None:
        """Remove the outline_toon modifier and its trailing mat.outline slot."""
        modifier = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
        if modifier is None:
            return
        slot_index = modifier.material_offset
        obj.modifiers.remove(modifier)
        slots = obj.data.materials
        if 0 <= slot_index < len(slots):
            if slots[slot_index] is not None and slots[slot_index].name.startswith(
                "mat.outline"
            ):
                obj.data.materials.pop(index=slot_index)

    @staticmethod
    def remove_all() -> None:
        """Strip outlines from pup.*/acc.* objects and purge mat.outline datablocks."""
        import bpy

        from puppet_pipeline.common import naming

        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects.get(object_name)
            if obj is not None:
                OutlineApplier.remove_from(obj)
        for obj in bpy.data.objects:
            if obj.name.startswith("acc."):
                OutlineApplier.remove_from(obj)
        for material in [
            m for m in bpy.data.materials if m.name.startswith("mat.outline")
        ]:
            bpy.data.materials.remove(material)
