from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_ENGINE = "BLENDER_EEVEE_NEXT"
FALLBACK_ENGINE = "BLENDER_WORKBENCH"
DEFAULT_PREVIEW_RESOLUTION = (640, 480)
DEFAULT_RENDER_RESOLUTION = (1920, 1080)

_SUN_NAME = "preview_sun"
_RESOLUTION = re.compile(r"^(\d+)x(\d+)$")
_MIN_DIM = 16
_MAX_DIM = 16384


def parse_resolution(value: str) -> tuple[int, int]:
    """Parse a WxH resolution string; bounds 16–16384 per dimension."""
    if not isinstance(value, str):
        raise ValueError(f"resolution must be a WxH string: {value!r}")
    match = _RESOLUTION.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"resolution must be in WxH form: {value!r}")
    width, height = int(match.group(1)), int(match.group(2))
    if not (_MIN_DIM <= width <= _MAX_DIM and _MIN_DIM <= height <= _MAX_DIM):
        raise ValueError(
            f"resolution dimensions must be between {_MIN_DIM} and {_MAX_DIM}: {value!r}"
        )
    return (width, height)


@dataclass(frozen=True)
class RenderProfile:
    """Engine + resolution + light-rig preferences for previews and the saved blend."""

    engine: str = DEFAULT_ENGINE
    preview_resolution: tuple[int, int] = DEFAULT_PREVIEW_RESOLUTION
    render_resolution: tuple[int, int] = DEFAULT_RENDER_RESOLUTION
    light_rig: str = "sun_ambient"

    @staticmethod
    def apply_engine(scene) -> str | None:
        """Prefer EEVEE; fall back to Workbench and return a warning string."""
        try:
            scene.render.engine = DEFAULT_ENGINE
            return None
        except TypeError:
            scene.render.engine = FALLBACK_ENGINE
            return "EEVEE unavailable; fell back to Workbench"

    @staticmethod
    def setup_light_rig(scene) -> dict:
        """Create the fixed world-ambient + angled-sun rig; returns created state."""
        import bpy

        world = scene.world
        if world is None:
            world = bpy.data.worlds.new("preview_world")
            scene.world = world
        world.use_nodes = True
        background = next(
            node for node in world.node_tree.nodes if node.type == "BACKGROUND"
        )
        background.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1.0)
        background.inputs["Strength"].default_value = 0.3

        light_data = bpy.data.lights.new(_SUN_NAME, type="SUN")
        light_data.energy = 2.0
        light_data.angle = 0.5
        light = bpy.data.objects.new(_SUN_NAME, light_data)
        scene.collection.objects.link(light)
        light.rotation_euler = (0.5236, 0.0, 0.3491)
        return {"world_created": world.name == "preview_world", "sun": light}

    @staticmethod
    def teardown_light_rig(scene, created: dict) -> None:
        """Remove the sun object/datablock created by setup_light_rig."""
        import bpy

        sun = created.get("sun")
        if sun is not None:
            data = sun.data
            bpy.data.objects.remove(sun, do_unlink=True)
            if data is not None and data.users == 0:
                bpy.data.lights.remove(data)
        if created.get("world_created"):
            world = scene.world
            scene.world = None
            if world is not None and world.users == 0:
                bpy.data.worlds.remove(world)

    def apply_to_blend(self, scene) -> dict:
        """Persist engine + render_resolution onto the saved blend; returns record."""
        warning = self.apply_engine(scene)
        scene.render.resolution_x, scene.render.resolution_y = self.render_resolution
        return {
            "engine": scene.render.engine,
            "resolution_x": scene.render.resolution_x,
            "resolution_y": scene.render.resolution_y,
            "warning": warning,
        }
