import json
import tempfile
import time
import unittest
from pathlib import Path

import bpy

import style_puppet
from puppet_pipeline.styling.materials import MaterialApplier
from tests.blender.fixtures import build_rig_fixture


class StylingSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        from puppet_pipeline.styling.presets import reset_styling

        reset_styling()
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.input_blend = self.dir / "puppet.blend"
        bpy.ops.wm.save_as_mainfile(
            filepath=str(self.input_blend), check_existing=False
        )
        (self.dir / "puppet.manifest.json").write_text(
            json.dumps({"parameters": {"limb_radius": 0.05}}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        from puppet_pipeline.styling.presets import reset_styling

        reset_styling()
        self.tmp.cleanup()

    def _run(self, *args: str) -> int:
        return style_puppet.main(
            ["blender", "--background", "--python", "style_puppet.py", "--", *args]
        )

    def test_single_material_apply_under_10_seconds(self) -> None:
        start = time.perf_counter()
        MaterialApplier.apply(bpy.data.objects["pup.torso"], "blue")
        self.assertLess(time.perf_counter() - start, 10.0)

    def test_full_styling_pipeline_under_60_seconds(self) -> None:
        output = self.dir / "styled.blend"
        manifest = self.dir / "styled.styling.json"
        start = time.perf_counter()
        code = self._run(
            "--input", str(self.input_blend),
            "--output", str(output),
            "--styling-manifest", str(manifest),
            "--material", "torso=blue",
            "--material", "head=red",
            "--accessory", "sneakers",
            "--background", "kitchen",
        )
        self.assertEqual(code, 0)
        self.assertLess(time.perf_counter() - start, 60.0)
        self.assertTrue(output.exists())
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "styling-v2")
        self.assertEqual(payload["background"], "kitchen")
        self.assertEqual(len(payload["accessories"]), 2)

    def test_rerun_is_idempotent(self) -> None:
        output = self.dir / "styled.blend"
        for _ in range(2):
            code = self._run(
                "--input", str(self.input_blend),
                "--output", str(output),
                "--material", "torso=blue",
            )
            self.assertEqual(code, 0)
        pipeline_objects = [
            o.name
            for o in bpy.data.objects
            if o.name.startswith(("pup.", "acc.", "bg.")) or o.name.startswith("rig")
        ]
        self.assertFalse(
            any(".001" in name for name in pipeline_objects),
            msg=f"numeric-suffixed objects: {[n for n in pipeline_objects if '.001' in n]}",
        )
        self.assertEqual(
            len([o for o in bpy.data.objects if o.name.startswith("acc.")]), 0,
        )

    def test_no_animation_data_created(self) -> None:
        output = self.dir / "styled.blend"
        code = self._run(
            "--input", str(self.input_blend),
            "--output", str(output),
            "--material", "torso=blue",
            "--accessory", "cap",
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(bpy.data.actions), 0)
        for obj in bpy.data.objects:
            self.assertIsNone(obj.animation_data, msg=f"{obj.name} has animation")
            for driver_list in (
                getattr(obj.data, "animation_data", None),
            ):
                self.assertIsNone(driver_list)

    def test_invalid_material_exits_nonzero_without_output(self) -> None:
        output = self.dir / "bad.blend"
        code = self._run(
            "--input", str(self.input_blend),
            "--output", str(output),
            "--material", "torso=not_a_preset",
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
