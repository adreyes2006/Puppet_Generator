from __future__ import annotations

from pathlib import Path

from mathutils import Vector

from puppet_pipeline.styling.materials import DEFAULT_LIMB_THICKNESS

_PREVIEW_KINDS = {"material", "accessory", "background"}
_HIDDEN_PREFIX = "preview_hidden."


class PreviewRenderer:
    """Renders non-destructive PNG previews of styling choices via Workbench."""

    @staticmethod
    def render(
        kind: str,
        name: str,
        preview_dir: Path | str,
        limb_thickness: float = DEFAULT_LIMB_THICKNESS,
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
            PreviewRenderer._render_to(target)
        finally:
            PreviewRenderer._restore(snapshot)
        return target

    @staticmethod
    def _snapshot() -> dict:
        import bpy

        from puppet_pipeline.common import naming

        material_slots = {}
        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects.get(object_name)
            if obj is not None:
                material_slots[object_name] = list(obj.data.materials)

        hidden = {}
        for obj in list(bpy.data.objects):
            if obj.name.startswith(("acc.", "bg.")):
                hidden[obj.name] = (obj, obj.hide_render, obj.hide_viewport)
                obj.name = f"{_HIDDEN_PREFIX}{obj.name}"
                obj.hide_render = True
                obj.hide_viewport = True

        scene = bpy.context.scene
        return {
            "material_slots": material_slots,
            "render": {
                "engine": scene.render.engine,
                "resolution_x": scene.render.resolution_x,
                "resolution_y": scene.render.resolution_y,
                "filepath": scene.render.filepath,
                "file_format": scene.render.image_settings.file_format,
                "camera": scene.camera,
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
            for modifier in [m for m in obj.modifiers if m.type == "WIREFRAME"]:
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
    def _render_to(target: Path) -> None:
        import bpy

        scene = bpy.context.scene
        try:
            scene.render.engine = "BLENDER_WORKBENCH"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE_NEXT"

        camera = PreviewRenderer._frame_camera()
        scene.camera = camera
        scene.render.resolution_x = 640
        scene.render.resolution_y = 480
        scene.render.filepath = str(target)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(camera, do_unlink=True)

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
