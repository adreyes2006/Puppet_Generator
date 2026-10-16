import unittest

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.rigging.binding import BindingApplier
from puppet_pipeline.generation.geometry import GeometryBuilder
from puppet_pipeline.generation.parts import build_part_specs
from puppet_pipeline.rigging.armature import ArmatureBuilder


class RigidBindingContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collections = reset_puppet_scene()
        self.parameters = PuppetParameters()
        self.parts = build_part_specs(self.parameters)
        self.objects = GeometryBuilder(self.collections.geometry).build(self.parts)
        self.topology_before = {
            name: (
                tuple(tuple(vertex.co) for vertex in obj.data.vertices),
                tuple(tuple(polygon.vertices) for polygon in obj.data.polygons),
            )
            for name, obj in self.objects.items()
        }
        specs = ArmatureBuilder.plan(self.parameters, self.parts)
        self.armature = ArmatureBuilder(self.collections.rig).build(specs)
        BindingApplier.bind(self.objects, self.armature)

    def tearDown(self) -> None:
        reset_puppet_scene()

    def test_each_object_has_exactly_one_matching_vertex_group(self) -> None:
        for object_name, expected_bone in naming.GEOMETRY_BINDINGS.items():
            obj = self.objects[object_name]
            with self.subTest(object_name=object_name):
                self.assertEqual(len(obj.vertex_groups), 1)
                self.assertEqual(obj.vertex_groups[0].name, expected_bone)
                self.assertIn(expected_bone, naming.DEFORMING_BONE_NAMES)
                self.assertNotIn(expected_bone, naming.CONTROL_BONE_NAMES)

    def test_every_vertex_has_exactly_one_assignment_at_weight_one(self) -> None:
        for object_name, obj in self.objects.items():
            expected_group = obj.vertex_groups[naming.GEOMETRY_BINDINGS[object_name]]
            with self.subTest(object_name=object_name):
                self.assertGreater(len(obj.data.vertices), 0)
                for vertex in obj.data.vertices:
                    self.assertEqual(len(vertex.groups), 1)
                    assignment = vertex.groups[0]
                    self.assertEqual(assignment.group, expected_group.index)
                    self.assertAlmostEqual(assignment.weight, 1.0, places=6)

    def test_each_object_has_one_armature_modifier_targeting_rig(self) -> None:
        for object_name, obj in self.objects.items():
            modifiers = [
                modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"
            ]
            with self.subTest(object_name=object_name):
                self.assertEqual(len(modifiers), 1)
                self.assertIs(modifiers[0].object, self.armature)

    def test_each_object_is_parented_to_armature_without_parent_inverse(self) -> None:
        for object_name, obj in self.objects.items():
            with self.subTest(object_name=object_name):
                self.assertIs(obj.parent, self.armature)
                self.assertEqual(obj.parent_type, "OBJECT")
                self.assertTrue(obj.matrix_parent_inverse.is_identity)

    def test_binding_does_not_change_geometry_topology_or_coordinates(self) -> None:
        for object_name, obj in self.objects.items():
            topology_after = (
                tuple(tuple(vertex.co) for vertex in obj.data.vertices),
                tuple(tuple(polygon.vertices) for polygon in obj.data.polygons),
            )
            with self.subTest(object_name=object_name):
                self.assertEqual(topology_after, self.topology_before[object_name])

    def test_rebinding_is_idempotent(self) -> None:
        BindingApplier.bind(self.objects, self.armature)

        for object_name, obj in self.objects.items():
            with self.subTest(object_name=object_name):
                self.assertEqual(len(obj.vertex_groups), 1)
                self.assertEqual(
                    len(
                        [
                            modifier
                            for modifier in obj.modifiers
                            if modifier.type == "ARMATURE"
                        ]
                    ),
                    1,
                )
                self.assertTrue(
                    all(len(vertex.groups) == 1 for vertex in obj.data.vertices)
                )


if __name__ == "__main__":
    unittest.main()
