import unittest

import bpy

from puppet_pipeline.common import naming
from puppet_pipeline.styling.materials import MaterialApplier
from tests.blender.fixtures import build_rig_fixture


class FillModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def _wireframes(self, obj):
        return [m for m in obj.modifiers if m.type == "WIREFRAME"]

    def test_outline_adds_wireframe_to_all_pup_objects(self) -> None:
        MaterialApplier.set_fill_mode("outline")
        for name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects[name]
            with self.subTest(name=name):
                modifiers = self._wireframes(obj)
                self.assertEqual(len(modifiers), 1)
                self.assertTrue(modifiers[0].use_replace)
                self.assertGreater(modifiers[0].thickness, 0.0)

    def test_wireframe_ordered_after_armature(self) -> None:
        MaterialApplier.set_fill_mode("outline")
        for name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects[name]
            with self.subTest(name=name):
                types = [m.type for m in obj.modifiers]
                self.assertEqual(types, ["ARMATURE", "WIREFRAME"])

    def test_solid_removes_wireframe_keeps_armature(self) -> None:
        MaterialApplier.set_fill_mode("outline")
        MaterialApplier.set_fill_mode("solid")
        for name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects[name]
            with self.subTest(name=name):
                self.assertEqual(self._wireframes(obj), [])
                self.assertEqual([m.type for m in obj.modifiers], ["ARMATURE"])

    def test_fill_mode_idempotent(self) -> None:
        MaterialApplier.set_fill_mode("outline")
        MaterialApplier.set_fill_mode("outline")
        for name in naming.GEOMETRY_BINDINGS:
            with self.subTest(name=name):
                self.assertEqual(len(self._wireframes(bpy.data.objects[name])), 1)

    def test_wireframe_never_added_to_non_pup_objects(self) -> None:
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = "acc.shoe.sneakers.L"
        MaterialApplier.set_fill_mode("outline")
        self.assertEqual(self._wireframes(cube), [])

    def test_fill_mode_rejects_invalid_value(self) -> None:
        with self.assertRaises(ValueError):
            MaterialApplier.set_fill_mode("shaded")


if __name__ == "__main__":
    unittest.main()
