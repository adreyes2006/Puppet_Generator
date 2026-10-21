import tempfile
import unittest
from pathlib import Path

import bpy

from puppet_pipeline.styling.preview import PreviewRenderer
from puppet_pipeline.styling.render import RenderProfile, parse_resolution
from tests.blender.fixtures import build_rig_fixture


class EngineSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.preview_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_preview_renders_with_eevee_or_fallback(self) -> None:
        PreviewRenderer.render("material", "blue", self.preview_dir)
        self.assertIn(
            PreviewRenderer.last_engine,
            ("BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"),
        )

    def test_light_rig_present_during_render(self) -> None:
        scene = bpy.context.scene
        created = RenderProfile.setup_light_rig(scene)
        try:
            sun = bpy.data.objects.get("preview_sun")
            self.assertIsNotNone(sun)
            self.assertEqual(sun.data.type, "SUN")
            self.assertIsNotNone(scene.world)
        finally:
            RenderProfile.teardown_light_rig(scene, created)
        self.assertIsNone(bpy.data.objects.get("preview_sun"))

    def test_scene_fully_restored_after_preview(self) -> None:
        scene = bpy.context.scene
        world_before = scene.world
        lights_before = {o.name for o in bpy.data.objects if o.type == "LIGHT"}
        engine_before = scene.render.engine
        PreviewRenderer.render("material", "red", self.preview_dir)
        self.assertIs(scene.world, world_before)
        self.assertEqual(
            {o.name for o in bpy.data.objects if o.type == "LIGHT"},
            lights_before,
        )
        self.assertEqual(scene.render.engine, engine_before)
        self.assertIsNone(bpy.data.objects.get("preview_sun"))


class ResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.preview_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_custom_preview_resolution_png_size(self) -> None:
        import struct

        path = PreviewRenderer.render(
            "material", "blue", self.preview_dir, resolution=(1280, 720)
        )
        header = path.read_bytes()[:24]
        width, height = struct.unpack(">II", header[16:24])
        self.assertEqual((width, height), (1280, 720))

    def test_parse_resolution_valid(self) -> None:
        self.assertEqual(parse_resolution("1280x720"), (1280, 720))

    def test_apply_to_blend_records_settings(self) -> None:
        scene = bpy.context.scene
        profile = RenderProfile(render_resolution=(1280, 720))
        record = profile.apply_to_blend(scene)
        try:
            self.assertEqual(scene.render.resolution_x, 1280)
            self.assertEqual(scene.render.resolution_y, 720)
            self.assertEqual(record["engine"], scene.render.engine)
            self.assertEqual(record["resolution_x"], 1280)
            self.assertEqual(record["resolution_y"], 720)
        finally:
            scene.render.resolution_x = 640
            scene.render.resolution_y = 480


if __name__ == "__main__":
    unittest.main()
