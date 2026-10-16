import unittest

from mathutils import Vector

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.rigging.armature import ArmatureBuilder
from puppet_pipeline.generation.parts import build_part_specs


DEFORMING_PARENTS = {
    "hips": None,
    "spine": "hips",
    "chest": "spine",
    "neck": "chest",
    "head": "neck",
    "shoulder.L": "chest",
    "shoulder.R": "chest",
    "upper_arm.L": "shoulder.L",
    "upper_arm.R": "shoulder.R",
    "forearm.L": "upper_arm.L",
    "forearm.R": "upper_arm.R",
    "hand.L": "forearm.L",
    "hand.R": "forearm.R",
    "thigh.L": "hips",
    "thigh.R": "hips",
    "shin.L": "thigh.L",
    "shin.R": "thigh.R",
    "foot.L": "shin.L",
    "foot.R": "shin.R",
}

CONNECTED_BONES = {
    "chest",
    "neck",
    "head",
    "shoulder.L",
    "shoulder.R",
    "upper_arm.L",
    "upper_arm.R",
    "forearm.L",
    "forearm.R",
    "hand.L",
    "hand.R",
    "shin.L",
    "shin.R",
    "foot.L",
    "foot.R",
}


class ArmatureContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = reset_puppet_scene()
        parameters = PuppetParameters()
        parts = build_part_specs(parameters)
        specs = ArmatureBuilder.plan(parameters, parts)
        self.armature_object = ArmatureBuilder(self.collections.rig).build(specs)
        self.bones = self.armature_object.data.bones

    def tearDown(self) -> None:
        reset_puppet_scene()

    def test_armature_names_type_and_collection_are_exact(self) -> None:
        self.assertEqual(self.armature_object.name, naming.ARMATURE_OBJECT_NAME)
        self.assertEqual(self.armature_object.data.name, naming.ARMATURE_DATA_NAME)
        self.assertEqual(self.armature_object.type, "ARMATURE")
        self.assertEqual(
            list(self.armature_object.users_collection),
            [self.collections.rig],
        )

    def test_exact_deforming_and_control_bone_sets_exist(self) -> None:
        deforming = {bone.name for bone in self.bones if bone.use_deform}
        controls = {bone.name for bone in self.bones if not bone.use_deform}

        self.assertEqual(deforming, set(naming.DEFORMING_BONE_NAMES))
        self.assertEqual(controls, set(naming.CONTROL_BONE_NAMES))
        self.assertEqual(len(deforming), 19)
        self.assertEqual(len(controls), 8)
        self.assertEqual(len(self.bones), 27)

    def test_deforming_bone_parent_hierarchy_is_exact(self) -> None:
        for bone_name, expected_parent in DEFORMING_PARENTS.items():
            bone = self.bones[bone_name]
            actual_parent = bone.parent.name if bone.parent else None
            with self.subTest(bone=bone_name):
                self.assertEqual(actual_parent, expected_parent)

    def test_control_bones_are_non_deforming_children_of_hips(self) -> None:
        for bone_name in naming.CONTROL_BONE_NAMES:
            bone = self.bones[bone_name]
            with self.subTest(bone=bone_name):
                self.assertFalse(bone.use_deform)
                self.assertIsNotNone(bone.parent)
                self.assertEqual(bone.parent.name, "hips")
                self.assertFalse(bone.use_connect)

    def test_connected_flags_and_joint_positions_match(self) -> None:
        for bone in self.bones:
            if bone.name in naming.CONTROL_BONE_NAMES or bone.name == "hips":
                continue
            with self.subTest(bone=bone.name):
                self.assertEqual(bone.use_connect, bone.name in CONNECTED_BONES)
                if bone.use_connect:
                    self.assertLess((bone.head_local - bone.parent.tail_local).length, 1e-6)

    def test_all_bones_and_roll_axes_follow_planar_convention(self) -> None:
        world_positive_y = Vector((0.0, 1.0, 0.0))
        local_positive_z = Vector((0.0, 0.0, 1.0))

        for bone in self.bones:
            local_z_in_armature = (
                bone.matrix_local.to_3x3() @ local_positive_z
            ).normalized()
            with self.subTest(bone=bone.name):
                if not bone.name.startswith(("elbow_pole.", "knee_pole.")):
                    self.assertAlmostEqual(bone.head_local.y, 0.0, places=6)
                    self.assertAlmostEqual(bone.tail_local.y, 0.0, places=6)
                self.assertGreater(local_z_in_armature.dot(world_positive_y), 0.99999)


if __name__ == "__main__":
    unittest.main()
