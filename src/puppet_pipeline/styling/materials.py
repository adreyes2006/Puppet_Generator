from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialPreset:
    name: str
    base_color: tuple[float, float, float, float]
    roughness: float = 0.5
    metallic: float = 0.0
    emission_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    emission_strength: float = 0.0
    fill_mode: str = "solid"


def _rgba(red: int, green: int, blue: int) -> tuple[float, float, float, float]:
    return (red / 255.0, green / 255.0, blue / 255.0, 1.0)


MATERIAL_CATALOG: dict[str, MaterialPreset] = {
    preset.name: preset
    for preset in (
        MaterialPreset("white", _rgba(245, 245, 245), roughness=0.6),
        MaterialPreset("grey", _rgba(158, 158, 158), roughness=0.6),
        MaterialPreset("black", _rgba(32, 32, 32), roughness=0.6),
        MaterialPreset("red", _rgba(211, 47, 47), roughness=0.55),
        MaterialPreset("blue", _rgba(25, 118, 210), roughness=0.55),
        MaterialPreset("green", _rgba(56, 142, 60), roughness=0.55),
        MaterialPreset("yellow", _rgba(251, 192, 45), roughness=0.55),
        MaterialPreset("purple", _rgba(123, 31, 162), roughness=0.55),
        MaterialPreset("orange", _rgba(230, 126, 34), roughness=0.55),
        MaterialPreset("skin_light", _rgba(255, 205, 178), roughness=0.7),
        MaterialPreset("skin_medium", _rgba(224, 172, 132), roughness=0.7),
        MaterialPreset("skin_dark", _rgba(141, 110, 89), roughness=0.7),
        MaterialPreset(
            "metallic",
            _rgba(176, 190, 197),
            roughness=0.25,
            metallic=0.9,
        ),
        MaterialPreset(
            "glow_cyan",
            _rgba(0, 188, 212),
            roughness=0.3,
            emission_color=_rgba(0, 188, 212),
            emission_strength=3.0,
        ),
        MaterialPreset(
            "glow_warm",
            _rgba(255, 167, 38),
            roughness=0.3,
            emission_color=_rgba(255, 167, 38),
            emission_strength=3.0,
        ),
    )
}


DEFAULT_LIMB_THICKNESS = 0.06


def _get_material(preset: MaterialPreset):
    import bpy

    from puppet_pipeline.styling import naming as styling_naming

    datablock_name = styling_naming.material_name(preset.name)
    material = bpy.data.materials.get(datablock_name)
    if material is None:
        material = bpy.data.materials.new(datablock_name)
    material.use_nodes = True
    principled = next(
        node
        for node in material.node_tree.nodes
        if node.type == "BSDF_PRINCIPLED"
    )
    principled.inputs["Base Color"].default_value = preset.base_color
    principled.inputs["Roughness"].default_value = preset.roughness
    principled.inputs["Metallic"].default_value = preset.metallic
    emission_color = principled.inputs.get("Emission Color") or principled.inputs.get(
        "Emission"
    )
    if emission_color is not None:
        emission_color.default_value = preset.emission_color
    emission_strength = principled.inputs.get("Emission Strength")
    if emission_strength is not None:
        emission_strength.default_value = preset.emission_strength
    material.diffuse_color = preset.base_color
    return material


class MaterialApplier:
    """Assigns catalog materials to objects and toggles the outline fill mode."""

    @staticmethod
    def apply(obj, preset_name: str) -> None:
        """Assign `mat.<preset>` to obj's first material slot via Principled inputs."""
        preset = MATERIAL_CATALOG.get(preset_name)
        if preset is None:
            raise ValueError(f"Unknown material preset: {preset_name!r}")
        material = _get_material(preset)
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material

    @staticmethod
    def set_fill_mode(mode: str, limb_thickness: float = DEFAULT_LIMB_THICKNESS) -> None:
        """Add ('outline') or remove ('solid') Wireframe modifiers on all pup.* parts."""
        import bpy

        from puppet_pipeline.common import naming

        if mode not in ("solid", "outline"):
            raise ValueError(f"fill mode must be 'solid' or 'outline': {mode!r}")
        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects.get(object_name)
            if obj is None:
                continue
            wireframes = [m for m in obj.modifiers if m.type == "WIREFRAME"]
            if mode == "solid":
                for modifier in wireframes:
                    obj.modifiers.remove(modifier)
            elif not wireframes:
                modifier = obj.modifiers.new(name="styling_outline", type="WIREFRAME")
                modifier.use_replace = True
                modifier.thickness = limb_thickness * 0.5
