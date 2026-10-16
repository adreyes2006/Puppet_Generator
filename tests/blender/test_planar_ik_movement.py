import unittest

from mathutils import Vector

from puppet_pipeline.verify.rig_check import RigVerificationError, RigVerifier
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.generation.geometry import GeometryBuilder
from puppet_pipeline.generation.parts import build_part_specs
from puppet_pipeline.rigging.armature import ArmatureBuilder
from puppet_pipeline.rigging.binding import BindingApplier
from puppet_pipeline.rigging.constraints import ConstraintBuilder
from tests.blender.fixtures import RigFixture, break_binding, break_ik_target


IK_MOVEMENTS = {
    "forearm.L": ("hand_ctrl.L", "elbow_pole.L", Vector((0.20, 0.0, -0.25))),
    "forearm.R": ("hand_ctrl.R", "elbow_pole.R", Vector((-0.20, 0.0, -0.25))),
    "shin.L": ("foot_ctrl.L", "knee_pole.L", Vector((-0.20, 0.0, 0.20))),
    "shin.R": ("foot_ctrl.R", "knee_pole.R", Vector((0.20, 0.0, 0.20))),
}


class PlanarIKMovementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = reset_puppet_scene()
        parameters = PuppetParameters()
        parts = build_part_specs(parameters)
        self.objects = GeometryBuilder(self.collections.geometry).build(parts)
        specs = ArmatureBuilder.plan(parameters, parts)
        self.armature = ArmatureBuilder(self.collections.rig).build(specs)
        ConstraintBuilder(self.armature).apply()
        BindingApplier.bind(self.objects, self.armature)
        self.fixture = RigFixture(
            collections=self.collections,
            parameters=parameters,
            parts=parts,
            objects=self.objects,
            armature=self.armature,
        )
        self.verifier = RigVerifier(self.armature, self.objects, epsilon=1e-5)

    def tearDown(self) -> None:
        reset_puppet_scene()

    def _pose_snapshot(self):
        return {
            bone.name: tuple(value for row in bone.matrix_basis for value in row)
            for bone in self.armature.pose.bones
        }

    def test_each_hand_and_foot_control_solves_its_two_bone_chain(self) -> None:
        for terminal, (control, pole, offset) in IK_MOVEMENTS.items():
            with self.subTest(terminal=terminal):
                report = self.verifier.verify_ik_control(
                    terminal,
                    control,
                    pole,
                    offset,
                )
                self.assertEqual(report.subject, terminal)
                self.assertEqual(report.control, control)
                self.assertGreater(report.moved_vertex_count, 0)
                self.assertLessEqual(report.target_distance_error, 5e-4)

    def test_ik_motion_remains_in_xz_plane(self) -> None:
        for terminal, (control, pole, offset) in IK_MOVEMENTS.items():
            with self.subTest(terminal=terminal):
                report = self.verifier.verify_ik_control(
                    terminal,
                    control,
                    pole,
                    offset,
                )
                self.assertLessEqual(report.max_y_displacement, 1e-5)

    def test_elbows_and_knees_bend_toward_their_configured_poles(self) -> None:
        for terminal, (control, pole, offset) in IK_MOVEMENTS.items():
            with self.subTest(terminal=terminal):
                report = self.verifier.verify_ik_control(
                    terminal,
                    control,
                    pole,
                    offset,
                )
                self.assertGreater(report.pole_alignment, 0.0)

    def test_each_ik_check_restores_the_entire_pose(self) -> None:
        for terminal, (control, pole, offset) in IK_MOVEMENTS.items():
            pose_before = self._pose_snapshot()
            with self.subTest(terminal=terminal):
                self.verifier.verify_ik_control(
                    terminal,
                    control,
                    pole,
                    offset,
                )
                self.assertEqual(self._pose_snapshot(), pose_before)

    def test_broken_binding_reports_object_and_bone(self) -> None:
        break_binding(self.fixture, "pup.forearm.L")

        with self.assertRaisesRegex(
            RigVerificationError,
            r"pup\.forearm\.L.*forearm\.L",
        ):
            self.verifier.verify_bone_rotation("forearm.L", 15.0)

    def test_broken_ik_target_reports_terminal_and_target(self) -> None:
        break_ik_target(self.fixture, "forearm.L")
        control, pole, offset = IK_MOVEMENTS["forearm.L"]

        with self.assertRaisesRegex(
            RigVerificationError,
            r"forearm\.L.*missing_ik_target.*hand_ctrl\.L",
        ):
            self.verifier.verify_ik_control(
                "forearm.L",
                control,
                pole,
                offset,
            )


if __name__ == "__main__":
    unittest.main()
