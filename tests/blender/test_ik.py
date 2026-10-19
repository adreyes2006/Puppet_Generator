import unittest

from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.rigging.constraints import ConstraintBuilder
from puppet_pipeline.rigging.armature import ArmatureBuilder
from puppet_pipeline.generation.parts import build_part_specs


IK_CHAINS = {
    "forearm.L": ("upper_arm.L", "hand_ctrl.L", "elbow_pole.L"),
    "forearm.R": ("upper_arm.R", "hand_ctrl.R", "elbow_pole.R"),
    "shin.L": ("thigh.L", "foot_ctrl.L", "knee_pole.L"),
    "shin.R": ("thigh.R", "foot_ctrl.R", "knee_pole.R"),
}


class PlanarIKContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = reset_puppet_scene()
        parameters = PuppetParameters()
        parts = build_part_specs(parameters)
        specs = ArmatureBuilder.plan(parameters, parts)
        self.armature = ArmatureBuilder(self.collections.rig).build(specs)
        ConstraintBuilder(self.armature).apply()

    def tearDown(self) -> None:
        reset_puppet_scene()

    def test_exactly_four_ik_constraints_exist_on_terminal_bones(self) -> None:
        owners = {
            pose_bone.name
            for pose_bone in self.armature.pose.bones
            if any(constraint.type == "IK" for constraint in pose_bone.constraints)
        }
        self.assertEqual(owners, set(IK_CHAINS))

        for terminal_name in IK_CHAINS:
            constraints = [
                constraint
                for constraint in self.armature.pose.bones[terminal_name].constraints
                if constraint.type == "IK"
            ]
            with self.subTest(terminal=terminal_name):
                self.assertEqual(len(constraints), 1)

    def test_ik_targets_poles_and_chain_counts_match_contract(self) -> None:
        for terminal_name, (_, target_name, pole_name) in IK_CHAINS.items():
            constraint = next(
                constraint
                for constraint in self.armature.pose.bones[terminal_name].constraints
                if constraint.type == "IK"
            )
            with self.subTest(terminal=terminal_name):
                self.assertIs(constraint.target, self.armature)
                self.assertEqual(constraint.subtarget, target_name)
                self.assertIs(constraint.pole_target, self.armature)
                self.assertEqual(constraint.pole_subtarget, pole_name)
                self.assertEqual(constraint.chain_count, 2)

    def test_each_ik_chain_uses_unrestricted_solver_axes(self) -> None:
        for terminal_name, (parent_name, _, _) in IK_CHAINS.items():
            for bone_name in (terminal_name, parent_name):
                pose_bone = self.armature.pose.bones[bone_name]
                with self.subTest(terminal=terminal_name, bone=bone_name):
                    self.assertFalse(pose_bone.use_ik_limit_x)
                    self.assertFalse(pose_bone.use_ik_limit_y)
                    self.assertFalse(pose_bone.use_ik_limit_z)

    def test_pole_controls_have_deterministic_in_plane_offsets(self) -> None:
        for pole_name in (
            "elbow_pole.L",
            "elbow_pole.R",
            "knee_pole.L",
            "knee_pole.R",
        ):
            pole = self.armature.data.bones[pole_name]
            with self.subTest(pole=pole_name):
                self.assertAlmostEqual(pole.head_local.y, 0.0, places=6)
                self.assertAlmostEqual(pole.tail_local.y, 0.0, places=6)

    def test_fk_limit_rotation_constraints_allow_only_local_y(self) -> None:
        ik_bones = {
            bone_name
            for terminal_name, (parent_name, _, _) in IK_CHAINS.items()
            for bone_name in (terminal_name, parent_name)
        }
        control_bones = {
            target_or_pole
            for _, target_name, pole_name in IK_CHAINS.values()
            for target_or_pole in (target_name, pole_name)
        }
        expected_fk_bones = {
            bone.name
            for bone in self.armature.data.bones
            if bone.use_deform
        } - ik_bones

        for bone_name in expected_fk_bones:
            constraints = [
                constraint
                for constraint in self.armature.pose.bones[bone_name].constraints
                if constraint.type == "LIMIT_ROTATION"
            ]
            with self.subTest(bone=bone_name):
                self.assertEqual(len(constraints), 1)
                constraint = constraints[0]
                self.assertEqual(constraint.owner_space, "LOCAL")
                self.assertTrue(constraint.use_limit_x)
                self.assertEqual(constraint.min_x, 0.0)
                self.assertEqual(constraint.max_x, 0.0)
                self.assertTrue(constraint.use_limit_y)
                self.assertEqual(constraint.min_y, 0.0)
                self.assertEqual(constraint.max_y, 0.0)
                self.assertFalse(constraint.use_limit_z)

        for bone_name in control_bones:
            with self.subTest(control=bone_name):
                self.assertFalse(
                    any(
                        constraint.type == "LIMIT_ROTATION"
                        for constraint in self.armature.pose.bones[bone_name].constraints
                    )
                )


if __name__ == "__main__":
    unittest.main()
