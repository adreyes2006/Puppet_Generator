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


class RigMovementVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = reset_puppet_scene()
        parameters = PuppetParameters()
        parts = build_part_specs(parameters)
        self.objects = GeometryBuilder(self.collections.geometry).build(parts)
        specs = ArmatureBuilder.plan(parameters, parts)
        self.armature = ArmatureBuilder(self.collections.rig).build(specs)
        ConstraintBuilder(self.armature).apply()
        BindingApplier.bind(self.objects, self.armature)
        self.verifier = RigVerifier(self.armature, self.objects, epsilon=1e-5)

    def tearDown(self) -> None:
        reset_puppet_scene()

    def _pose_snapshot(self):
        return {
            bone.name: tuple(value for row in bone.matrix_basis for value in row)
            for bone in self.armature.pose.bones
        }

    def test_positive_and_negative_fk_rotation_move_only_bound_geometry(self) -> None:
        for angle in (-15.0, 15.0):
            with self.subTest(angle=angle):
                report = self.verifier.verify_bone_rotation("head", angle)
                self.assertEqual(report.subject, "head")
                self.assertEqual(
                    report.moved_vertex_count,
                    len(self.objects["pup.head"].data.vertices),
                )
                self.assertGreater(report.max_bound_displacement, 1e-5)
                self.assertLessEqual(report.max_unrelated_displacement, 1e-5)

    def test_root_translation_moves_every_evaluated_vertex_by_offset(self) -> None:
        offset = Vector((0.25, 0.0, 0.1))

        report = self.verifier.verify_root_translation(offset)

        self.assertEqual(report.subject, "hips")
        self.assertEqual(report.moved_object_count, 14)
        self.assertEqual(
            report.moved_vertex_count,
            sum(len(obj.data.vertices) for obj in self.objects.values()),
        )
        self.assertLessEqual(report.max_translation_error, 1e-5)

    def test_verification_reads_evaluated_modifier_output(self) -> None:
        before = self.verifier.capture_evaluated_vertices()
        source_before = tuple(
            self.objects["pup.head"].matrix_world @ vertex.co
            for vertex in self.objects["pup.head"].data.vertices
        )
        pose_bone = self.armature.pose.bones["head"]
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler.z = 0.25
        self.armature.update_tag()
        self.verifier.update_scene()
        after = self.verifier.capture_evaluated_vertices()

        source_after = tuple(
            self.objects["pup.head"].matrix_world @ vertex.co
            for vertex in self.objects["pup.head"].data.vertices
        )

        self.assertNotEqual(before["pup.head"], after["pup.head"])
        self.assertEqual(source_before, source_after)
        self.verifier.reset_pose()

    def test_epsilon_failure_restores_entire_pose(self) -> None:
        pose_before = self._pose_snapshot()
        strict_verifier = RigVerifier(self.armature, self.objects, epsilon=100.0)

        with self.assertRaisesRegex(
            RigVerificationError,
            r"head.*did not move",
        ):
            strict_verifier.verify_bone_rotation("head", 15.0)

        self.assertEqual(self._pose_snapshot(), pose_before)

    def test_successful_checks_restore_entire_pose(self) -> None:
        pose_before = self._pose_snapshot()

        self.verifier.verify_bone_rotation("head", 15.0)
        self.assertEqual(self._pose_snapshot(), pose_before)

        self.verifier.verify_root_translation(Vector((0.25, 0.0, 0.1)))
        self.assertEqual(self._pose_snapshot(), pose_before)


if __name__ == "__main__":
    unittest.main()
