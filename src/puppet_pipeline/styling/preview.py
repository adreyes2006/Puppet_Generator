from __future__ import annotations

from pathlib import Path

from mathutils import Vector

from puppet_pipeline.styling.materials import DEFAULT_LIMB_THICKNESS

_PREVIEW_KINDS = {"material", "accessory", "background"}
_HIDDEN_PREFIX = "preview_hidden."


class PreviewRenderer:
    """Renders non-destructive PNG previews of styling choices via EEVEE."""

    last_engine: str | None = None

    @staticmethod
    def render(
        kind: str,
        name: str,
        preview_dir: Path | str,
        limb_thickness: float = DEFAULT_LIMB_THICKNESS,
        resolution: tuple[int, int] | None = None,
    ) -> Path:
        """Render `<kind>-<name>.png` into `preview_dir`, restoring the scene after."""
        import bpy

        if kind not in _PREVIEW_KINDS:
            raise ValueError(
                f"Unknown preview kind: {kind!r}; "
                f"expected one of {sorted(_PREVIEW_KINDS)}"
            )
        output_dir = Path(preview_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / f"{kind}-{name}.png"

        snapshot = PreviewRenderer._snapshot()
        try:
            PreviewRenderer._apply_preview(kind, name, limb_thickness)
            PreviewRenderer._render_to(target, resolution)
        finally:
            PreviewRenderer._restore(snapshot)
        return target

    @staticmethod
    def _snapshot() -> dict:
        import bpy

        from puppet_pipeline.common import naming

        material_slots = {}
        object_modifiers = {}
        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects.get(object_name)
            if obj is not None:
                material_slots[object_name] = list(obj.data.materials)
                object_modifiers[object_name] = {
                    m.name for m in obj.modifiers
                }

        hidden = {}
        for obj in list(bpy.data.objects):
            if obj.name.startswith(("acc.", "bg.")):
                hidden[obj.name] = (obj, obj.hide_render, obj.hide_viewport)
                obj.name = f"{_HIDDEN_PREFIX}{obj.name}"
                obj.hide_render = True
                obj.hide_viewport = True

        scene = bpy.context.scene
        world = scene.world
        return {
            "material_slots": material_slots,
            "object_modifiers": object_modifiers,
            "render": {
                "engine": scene.render.engine,
                "resolution_x": scene.render.resolution_x,
                "resolution_y": scene.render.resolution_y,
                "filepath": scene.render.filepath,
                "file_format": scene.render.image_settings.file_format,
                "camera": scene.camera,
            },
            "world": {
                "world": world,
                "color": tuple(world.color) if world is not None else None,
                "use_nodes": world.use_nodes if world is not None else None,
                "bg_color": (
                    tuple(
                        next(
                            n
                            for n in world.node_tree.nodes
                            if n.type == "BACKGROUND"
                        ).inputs["Color"].default_value
                    )
                    if world is not None and world.use_nodes
                    else None
                ),
                "bg_strength": (
                    next(
                        n
                        for n in world.node_tree.nodes
                        if n.type == "BACKGROUND"
                    ).inputs["Strength"].default_value
                    if world is not None and world.use_nodes
                    else None
                ),
            },
            "hidden": hidden,
            "objects": {o.name for o in bpy.data.objects},
            "meshes": {m.name for m in bpy.data.meshes},
            "materials": {m.name for m in bpy.data.materials},
            "collections": {c.name for c in bpy.data.collections},
        }

    @staticmethod
    def _restore(snapshot: dict) -> None:
        import bpy

        for obj in [
            o for o in bpy.data.objects if o.name not in snapshot["objects"]
        ]:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)

        for object_name, slots in snapshot["material_slots"].items():
            obj = bpy.data.objects.get(object_name)
            if obj is None:
                continue
            kept = snapshot["object_modifiers"].get(object_name, set())
            for modifier in [
                m for m in obj.modifiers if m.name not in kept
            ]:
                obj.modifiers.remove(modifier)
            obj.data.materials.clear()
            for material in slots:
                obj.data.materials.append(material)

        for material in [
            m for m in bpy.data.materials if m.name not in snapshot["materials"]
        ]:
            bpy.data.materials.remove(material)
        for mesh in [
            m for m in bpy.data.meshes if m.name not in snapshot["meshes"]
        ]:
            bpy.data.meshes.remove(mesh)
        for collection in [
            c
            for c in bpy.data.collections
            if c.name not in snapshot["collections"]
        ]:
            bpy.data.collections.remove(collection)

        for original_name, (obj, hide_render, hide_viewport) in snapshot[
            "hidden"
        ].items():
            obj.name = original_name
            obj.hide_render = hide_render
            obj.hide_viewport = hide_viewport

        render = snapshot["render"]
        scene = bpy.context.scene
        scene.render.engine = render["engine"]
        scene.render.resolution_x = render["resolution_x"]
        scene.render.resolution_y = render["resolution_y"]
        scene.render.filepath = render["filepath"]
        scene.render.image_settings.file_format = render["file_format"]
        scene.camera = render["camera"]

        world_state = snapshot["world"]
        scene.world = world_state["world"]
        world = scene.world
        if world is not None:
            world.color = world_state["color"]
            world.use_nodes = world_state["use_nodes"]
            if world.use_nodes and world_state["bg_color"] is not None:
                background = next(
                    n for n in world.node_tree.nodes if n.type == "BACKGROUND"
                )
                background.inputs["Color"].default_value = world_state["bg_color"]
                background.inputs["Strength"].default_value = world_state[
                    "bg_strength"
                ]

    @staticmethod
    def _apply_preview(kind: str, name: str, limb_thickness: float) -> None:
        import bpy

        from puppet_pipeline.common import naming
        from puppet_pipeline.styling.accessories import AccessoryBuilder
        from puppet_pipeline.styling.backgrounds import BackgroundBuilder
        from puppet_pipeline.styling.materials import MaterialApplier

        if kind == "material":
            for object_name in naming.GEOMETRY_BINDINGS:
                obj = bpy.data.objects.get(object_name)
                if obj is not None:
                    MaterialApplier.apply(obj, name)
        elif kind == "accessory":
            AccessoryBuilder.build(name, limb_thickness=limb_thickness)
        else:
            BackgroundBuilder.build(name)

    @staticmethod
    def _render_to(target: Path, resolution: tuple[int, int] | None = None) -> None:
        import bpy

        from puppet_pipeline.styling.render import FALLBACK_ENGINE, RenderProfile

        scene = bpy.context.scene
        warning = RenderProfile.apply_engine(scene)
        if warning:
            print(f"Warning: {warning}")
        PreviewRenderer.last_engine = scene.render.engine

        rig = (
            RenderProfile.setup_light_rig(scene)
            if scene.render.engine != FALLBACK_ENGINE
            else None
        )
        camera = PreviewRenderer._frame_camera()
        scene.camera = camera
        width, height = resolution or RenderProfile().preview_resolution
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.filepath = str(target)
        scene.render.image_settings.file_format = "PNG"
        try:
            bpy.ops.render.render(write_still=True)
        finally:
            bpy.data.objects.remove(camera, do_unlink=True)
            if rig is not None:
                RenderProfile.teardown_light_rig(scene, rig)

    @staticmethod
    def _frame_camera():
        import bpy

        from puppet_pipeline.common import naming

        min_x, max_x = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")
        for object_name in list(naming.GEOMETRY_BINDINGS) + [
            o.name for o in bpy.data.objects if o.name.startswith("acc.")
        ]:
            obj = bpy.data.objects.get(object_name)
            if obj is None or not hasattr(obj, "bound_box"):
                continue
            for corner in obj.bound_box:
                world = obj.matrix_world @ Vector(corner)
                min_x, max_x = min(min_x, world.x), max(max_x, world.x)
                min_z, max_z = min(min_z, world.z), max(max_z, world.z)
        if min_x == float("inf"):
            min_x, max_x, min_z, max_z = -1.0, 1.0, 0.0, 2.0

        width = max(max_x - min_x, 0.5)
        height = max(max_z - min_z, 0.5)
        center = Vector(((min_x + max_x) / 2, 0.0, (min_z + max_z) / 2))

        camera_data = bpy.data.cameras.new("preview_camera")
        camera = bpy.data.objects.new("preview_camera", camera_data)
        bpy.context.scene.collection.objects.link(camera)
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = max(width, height) * 1.3
        distance = 5.0
        camera.location = (center.x, center.y - distance, center.z)
        camera.rotation_euler = (1.5708, 0.0, 0.0)
        return camera
