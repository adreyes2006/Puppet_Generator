import unittest

import bpy

from puppet_pipeline.common import naming
from puppet_pipeline.styling.accessories import AccessoryBuilder
from puppet_pipeline.styling.outline import (
    OUTLINE_MATERIAL_NAME,
    OUTLINE_MODIFIER_NAME,
    OutlineApplier,
    OutlineSpec,
)
from puppet_pipeline.styling.presets import reset_styling
from tests.blender.fixtures import build_rig_fixture


def _outlined_objects():
    return [
        o
        for o in bpy.data.objects
        if o.name.startswith(("pup.", "acc."))
        and any(m.name == OUTLINE_MODIFIER_NAME for m in o.modifiers)
    ]


class OutlineApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def test_apply_all_covers_pup_objects(self) -> None:
        OutlineApplier.apply_all(OutlineSpec(enabled=True), 0.10)
        for object_name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects[object_name]
            modifier = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
            self.assertIsNotNone(modifier, object_name)
            self.assertEqual(modifier.type, "SOLIDIFY")
            self.assertTrue(modifier.use_flip_normals)
            self.assertTrue(modifier.use_even_offset)
            self.assertLess(modifier.offset, 0)
            self.assertAlmostEqual(modifier.thickness, 0.10 * 0.15)
            slot = obj.data.materials[modifier.material_offset]
            self.assertTrue(slot.name.startswith(OUTLINE_MATERIAL_NAME))

    def test_accessories_also_outlined(self) -> None:
        AccessoryBuilder.build("sneakers", "foot.L", 0.10)
        OutlineApplier.apply_all(OutlineSpec(enabled=True), 0.10)
        acc = [
            o for o in bpy.data.objects if o.name.startswith("acc.")
        ]
        self.assertTrue(acc)
        for obj in acc:
            self.assertIsNotNone(obj.modifiers.get(OUTLINE_MODIFIER_NAME))

    def test_background_objects_not_outlined(self) -> None:
        from puppet_pipeline.styling.backgrounds import BackgroundBuilder

        BackgroundBuilder.build("playground")
        OutlineApplier.apply_all(OutlineSpec(enabled=True), 0.10)
        for obj in bpy.data.objects:
            if obj.name.startswith("bg."):
                self.assertIsNone(obj.modifiers.get(OUTLINE_MODIFIER_NAME))

    def test_idempotent_reapply(self) -> None:
        spec = OutlineSpec(enabled=True)
        OutlineApplier.apply_all(spec, 0.10)
        before = len(_outlined_objects())
        OutlineApplier.apply_all(spec, 0.10)
        self.assertEqual(len(_outlined_objects()), before)
        obj = bpy.data.objects["pup.head"]
        modifiers = [
            m for m in obj.modifiers if m.name == OUTLINE_MODIFIER_NAME
        ]
        self.assertEqual(len(modifiers), 1)

    def test_reset_removes_everything(self) -> None:
        OutlineApplier.apply_all(OutlineSpec(enabled=True), 0.10)
        self.assertTrue(_outlined_objects())
        reset_styling()
        self.assertEqual(_outlined_objects(), [])
        self.assertFalse(
            any(
                m.name.startswith(OUTLINE_MATERIAL_NAME)
                for m in bpy.data.materials
            )
        )

    def test_custom_thickness_and_color(self) -> None:
        spec = OutlineSpec(enabled=True, thickness=0.05, color="#ff0000")
        OutlineApplier.apply_all(spec, 0.10)
        obj = bpy.data.objects["pup.head"]
        modifier = obj.modifiers.get(OUTLINE_MODIFIER_NAME)
        self.assertAlmostEqual(modifier.thickness, 0.05)
        material = bpy.data.materials[OUTLINE_MATERIAL_NAME]
        principled = next(
            n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"
        )
        color = principled.inputs["Base Color"].default_value
        self.assertAlmostEqual(color[0], 1.0, places=4)
        self.assertAlmostEqual(color[1], 0.0, places=4)


class OutlineFillModeExclusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def tearDown(self) -> None:
        reset_styling()


if __name__ == "__main__":
    unittest.main()
