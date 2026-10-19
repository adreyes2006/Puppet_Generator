import tempfile
import time
import unittest
from pathlib import Path

import bpy

import generate_puppet
from puppet_pipeline.common import naming
from puppet_pipeline.common.scene import reset_puppet_scene


class GenerationSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_directory = Path(self.temporary_directory.name)
        reset_puppet_scene()

    def tearDown(self) -> None:
        reset_puppet_scene()
        self.temporary_directory.cleanup()

    def _run_generation(self, output_name: str, *arguments: str) -> Path:
        output_path = self.output_directory / output_name
        status = generate_puppet.main(
            [
                "blender",
                "--background",
                "--",
                *arguments,
                "--output",
                str(output_path),
            ]
        )
        self.assertEqual(status, 0)
        return output_path

    def test_default_generation_saves_complete_blend_under_sixty_seconds(self) -> None:
        started_at = time.monotonic()
        output_path = self._run_generation("default-puppet.blend")
        elapsed = time.monotonic() - started_at

        self.assertTrue(output_path.is_file())
        self.assertEqual(Path(bpy.data.filepath).resolve(), output_path.resolve())
        self.assertLess(elapsed, 60.0)
        self.assertEqual(
            {name for name in naming.GEOMETRY_BINDINGS if name in bpy.data.objects},
            set(naming.GEOMETRY_BINDINGS),
        )
        armature = bpy.data.objects[naming.ARMATURE_OBJECT_NAME]
        self.assertEqual(armature.type, "ARMATURE")
        self.assertEqual(len(armature.data.bones), 27)

    def test_custom_generation_changes_lengths_and_thickness_by_twenty_percent(self) -> None:
        self._run_generation("default.blend")
        default_arm_length = max(bpy.data.objects["pup.upper_arm.L"].dimensions)
        default_leg_length = max(bpy.data.objects["pup.thigh.L"].dimensions)
        default_thickness = sorted(bpy.data.objects["pup.forearm.L"].dimensions)[1]

        custom_path = self._run_generation(
            "custom.blend",
            "--upper-arm-length",
            "1.5",
            "--forearm-length",
            "1.3",
            "--thigh-length",
            "1.6",
            "--shin-length",
            "1.4",
            "--limb-thickness",
            "0.10",
            "--seed",
            "42",
        )

        self.assertTrue(custom_path.is_file())
        self.assertGreater(
            max(bpy.data.objects["pup.upper_arm.L"].dimensions),
            default_arm_length * 1.2,
        )
        self.assertGreater(
            max(bpy.data.objects["pup.thigh.L"].dimensions),
            default_leg_length * 1.2,
        )
        self.assertGreater(
            sorted(bpy.data.objects["pup.forearm.L"].dimensions)[1],
            default_thickness * 1.2,
        )

    def test_same_session_rerun_leaves_exactly_one_puppet(self) -> None:
        self._run_generation("first.blend")
        self._run_generation("second.blend")

        self.assertEqual(
            sum(name in bpy.data.objects for name in naming.GEOMETRY_BINDINGS),
            14,
        )
        self.assertEqual(
            sum(
                obj.name == naming.ARMATURE_OBJECT_NAME
                for obj in bpy.data.objects
            ),
            1,
        )
        for collection_name in (
            naming.ROOT_COLLECTION_NAME,
            naming.GEOMETRY_COLLECTION_NAME,
            naming.RIG_COLLECTION_NAME,
        ):
            with self.subTest(collection=collection_name):
                self.assertEqual(
                    sum(
                        collection.name == collection_name
                        for collection in bpy.data.collections
                    ),
                    1,
                )
        self.assertFalse(
            any(
                naming.has_blender_numeric_suffix(data.name)
                for data_collection in (
                    bpy.data.objects,
                    bpy.data.collections,
                    bpy.data.meshes,
                    bpy.data.armatures,
                )
                for data in data_collection
                if data.name.startswith(("pup.", "PUPPET", "rig"))
            )
        )

    def test_generation_creates_no_animation_stage_data(self) -> None:
        self._run_generation("no-animation.blend")

        self.assertNotIn(naming.ANIMATION_COLLECTION_NAME, bpy.data.collections)
        self.assertEqual(len(bpy.data.actions), 0)
        for obj in bpy.data.objects:
            with self.subTest(obj=obj.name):
                animation_data = obj.animation_data
                self.assertTrue(
                    animation_data is None
                    or (
                        animation_data.action is None
                        and len(animation_data.drivers) == 0
                    )
                )

    def test_invalid_input_creates_no_partial_output(self) -> None:
        output_path = self.output_directory / "invalid.blend"
        status = generate_puppet.main(
            [
                "blender",
                "--background",
                "--",
                "--upper-arm-length",
                "-1",
                "--output",
                str(output_path),
            ]
        )

        self.assertNotEqual(status, 0)
        self.assertFalse(output_path.exists())
        self.assertFalse(output_path.with_suffix(".manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
