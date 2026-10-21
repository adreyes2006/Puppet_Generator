import unittest

import bpy
from mathutils import Vector

from puppet_pipeline.styling import naming as styling_naming
from puppet_pipeline.styling.accessories import (
    ACCESSORY_CATALOG,
    AccessoryBuilder,
)
from tests.blender.fixtures import build_rig_fixture


class AccessoryCatalogTests(unittest.TestCase):
    def test_catalog_has_three_shoe_and_three_hat_styles(self) -> None:
        shoes = [s for s in ACCESSORY_CATALOG.values() if s.kind == "shoe"]
        hats = [s for s in ACCESSORY_CATALOG.values() if s.kind == "hat"]
        self.assertGreaterEqual(len(shoes), 3)
        self.assertGreaterEqual(len(hats), 3)

    def test_specs_use_allowed_primitives(self) -> None:
        for style, spec in ACCESSORY_CATALOG.items():
            with self.subTest(style=style):
                self.assertGreaterEqual(len(spec.primitives), 1)
                self.assertLessEqual(len(spec.primitives), 4)
                for primitive in spec.primitives:
                    self.assertIn(primitive.kind, {"box", "cylinder", "sphere"})


class AccessoryBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def tearDown(self) -> None:
        for obj in list(bpy.data.objects):
            if obj.name.startswith("acc."):
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)

    def test_shoe_style_expands_to_both_feet(self) -> None:
        result = AccessoryBuilder.build("sneakers")
        self.assertEqual(len(result), 2)
        for side in ("L", "R"):
            obj = bpy.data.objects[f"acc.shoe.sneakers.{side}"]
            self.assertIsNotNone(obj)
            self.assertIs(obj.parent, self.fixture.armature)
            self.assertEqual(obj.parent_type, "BONE")
            self.assertEqual(obj.parent_bone, f"foot.{side}")

    def test_accessory_lands_in_style_collection_only(self) -> None:
        AccessoryBuilder.build("sneakers")
        obj = bpy.data.objects["acc.shoe.sneakers.L"]
        collections = [c.name for c in obj.users_collection]
        self.assertEqual(collections, [styling_naming.ACCESSORY_COLLECTION_NAME])

    def test_hat_parents_to_head_bone(self) -> None:
        AccessoryBuilder.build("cap")
        obj = bpy.data.objects["acc.hat.cap"]
        self.assertEqual(obj.parent_type, "BONE")
        self.assertEqual(obj.parent_bone, "head")

    def test_accessory_has_no_vertex_groups_or_armature_modifier(self) -> None:
        AccessoryBuilder.build("cap")
        obj = bpy.data.objects["acc.hat.cap"]
        self.assertEqual(len(obj.vertex_groups), 0)
        self.assertNotIn("ARMATURE", [m.type for m in obj.modifiers])

    def test_shoe_sits_near_foot_bone(self) -> None:
        AccessoryBuilder.build("sneakers")
        obj = bpy.data.objects["acc.shoe.sneakers.L"]
        rig = self.fixture.armature
        pose_bone = rig.pose.bones["foot.L"]
        bone_length = rig.data.bones["foot.L"].length
        midpoint = rig.matrix_world @ (
            pose_bone.matrix @ Vector((0.0, bone_length / 2, 0.0))
        )
        self.assertLess(
            (obj.matrix_world.translation - midpoint).length,
            0.5,
        )

    def test_explicit_bone_builds_single_side(self) -> None:
        result = AccessoryBuilder.build("sneakers", "foot.R")
        self.assertEqual(len(result), 1)
        self.assertIsNotNone(bpy.data.objects.get("acc.shoe.sneakers.R"))
        self.assertIsNone(bpy.data.objects.get("acc.shoe.sneakers.L"))

    def test_remove_deletes_object_and_mesh(self) -> None:
        AccessoryBuilder.build("sneakers")
        AccessoryBuilder.remove("acc.shoe.sneakers.L")
        self.assertIsNone(bpy.data.objects.get("acc.shoe.sneakers.L"))
        self.assertIsNone(bpy.data.meshes.get("acc.shoe.sneakers.L"))
        self.assertIsNotNone(bpy.data.objects.get("acc.shoe.sneakers.R"))

    def test_remove_unknown_name_is_noop(self) -> None:
        AccessoryBuilder.remove("acc.nothing")

    def test_unknown_style_raises(self) -> None:
        with self.assertRaises(ValueError):
            AccessoryBuilder.build("wings")

    def test_shoe_rejects_head_bone(self) -> None:
        with self.assertRaises(ValueError):
            AccessoryBuilder.build("sneakers", "head")


class AccessoryFollowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        AccessoryBuilder.build("sneakers")

    def tearDown(self) -> None:
        for obj in list(bpy.data.objects):
            if obj.name.startswith("acc."):
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        self.fixture.armature.pose.bones["foot_ctrl.L"].location = Vector((0, 0, 0))

    def test_accessory_follows_controlled_bone(self) -> None:
        left = bpy.data.objects["acc.shoe.sneakers.L"]
        right = bpy.data.objects["acc.shoe.sneakers.R"]
        before_l = left.matrix_world.translation.copy()
        before_r = right.matrix_world.translation.copy()

        self.fixture.armature.pose.bones["foot_ctrl.L"].location = Vector((0.5, 0.0, 0.0))
        bpy.context.view_layer.update()

        after_l = left.matrix_world.translation
        after_r = right.matrix_world.translation
        self.assertGreater((after_l - before_l).length, 0.2)
        self.assertAlmostEqual(after_r.x, before_r.x, places=4)
        self.assertAlmostEqual(after_r.z, before_r.z, places=4)


if __name__ == "__main__":
    unittest.main()
