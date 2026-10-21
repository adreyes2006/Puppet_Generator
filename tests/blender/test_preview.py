import tempfile
import unittest
from pathlib import Path

import bpy

from puppet_pipeline.styling.preview import PreviewRenderer
from tests.blender.fixtures import build_rig_fixture


def _scene_signature():
    return (
        len(bpy.data.objects),
        sorted(m.name for m in bpy.data.materials),
        sorted(c.name for c in bpy.data.collections),
    )


class PreviewRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.preview_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_material_preview_writes_nonempty_png(self) -> None:
        before = _scene_signature()
        path = PreviewRenderer.render("material", "blue", self.preview_dir)
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "material-blue.png")
        self.assertGreater(path.stat().st_size, 100)
        with path.open("rb") as fh:
            self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")

    def test_scene_restored_after_preview(self) -> None:
        before = _scene_signature()
        engine_before = bpy.context.scene.render.engine
        res_before = (
            bpy.context.scene.render.resolution_x,
            bpy.context.scene.render.resolution_y,
        )
        PreviewRenderer.render("material", "metallic", self.preview_dir)
        self.assertEqual(_scene_signature(), before)
        self.assertEqual(bpy.context.scene.render.engine, engine_before)
        self.assertEqual(
            (
                bpy.context.scene.render.resolution_x,
                bpy.context.scene.render.resolution_y,
            ),
            res_before,
        )

    def test_each_kind_produces_distinct_png(self) -> None:
        material_path = PreviewRenderer.render("material", "red", self.preview_dir)
        accessory_path = PreviewRenderer.render(
            "accessory", "sneakers", self.preview_dir
        )
        background_path = PreviewRenderer.render(
            "background", "kitchen", self.preview_dir
        )
        names = {material_path.name, accessory_path.name, background_path.name}
        self.assertEqual(len(names), 3)
        for path in (material_path, accessory_path, background_path):
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 100)

    def test_unknown_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            PreviewRenderer.render("pose", "blue", self.preview_dir)


if __name__ == "__main__":
    unittest.main()
