import unittest

import bpy
from mathutils import Vector

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.generation.geometry import GeometryBuilder
from puppet_pipeline.generation.parts import build_part_specs


class GeometryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = PuppetParameters(
            upper_arm_len=1.5,
            forearm_len=1.3,
            thigh_len=1.6,
            shin_len=1.4,
            limb_radius=0.1,
            torso_len=1.8,
            head_radius=0.3,
            hip_width=0.4,
            shoulder_width=0.7,
            seed=42,
        )
        self.collections = reset_puppet_scene()
        self.parts = build_part_specs(self.parameters)
        self.objects = GeometryBuilder(self.collections.geometry).build(self.parts)

    def tearDown(self) -> None:
        reset_puppet_scene()

    @staticmethod
    def _world_vertices(obj):
        return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]

    @staticmethod
    def _extent(vertices, axis) -> float:
        projections = [vertex.dot(axis) for vertex in vertices]
        return max(projections) - min(projections)

    def test_object_names_match_contract_exactly(self) -> None:
        self.assertEqual(set(self.objects), set(naming.GEOMETRY_BINDINGS))
        self.assertEqual(
            {obj.name for obj in self.objects.values()},
            set(naming.GEOMETRY_BINDINGS),
        )
        self.assertFalse(
            any(naming.has_blender_numeric_suffix(name) for name in self.objects)
        )

    def test_all_objects_are_meshes_with_positive_vertex_counts(self) -> None:
        for part in self.parts:
            obj = self.objects[part.name]
            with self.subTest(part=part.name):
                self.assertEqual(obj.type, "MESH")
                self.assertGreater(len(obj.data.vertices), 0)
                self.assertGreater(len(obj.data.polygons), 0)

    def test_objects_belong_only_to_geometry_collection(self) -> None:
        expected_collection = self.collections.geometry
        for obj in self.objects.values():
            with self.subTest(obj=obj.name):
                self.assertIn(obj, expected_collection.objects.values())
                self.assertEqual(list(obj.users_collection), [expected_collection])

    def test_geometry_is_centered_on_the_xz_plane(self) -> None:
        for part in self.parts:
            vertices = self._world_vertices(self.objects[part.name])
            y_coordinates = [vertex.y for vertex in vertices]
            with self.subTest(part=part.name):
                self.assertAlmostEqual(
                    (max(y_coordinates) + min(y_coordinates)) / 2,
                    0.0,
                    places=6,
                )
                self.assertLessEqual(
                    max(y_coordinates) - min(y_coordinates),
                    part.radius * 2 + 1e-6,
                )

    def test_geometry_dimensions_match_part_specs(self) -> None:
        for part in self.parts:
            vertices = self._world_vertices(self.objects[part.name])
            direction = Vector(part.direction).normalized()
            perpendicular = Vector((-direction.z, 0.0, direction.x)).normalized()
            with self.subTest(part=part.name):
                self.assertAlmostEqual(
                    self._extent(vertices, direction),
                    part.length,
                    places=5,
                )
                self.assertAlmostEqual(
                    self._extent(vertices, perpendicular),
                    part.radius * 2,
                    places=5,
                )

    def test_custom_parameters_change_expected_dimensions(self) -> None:
        expected_lengths = {
            "pup.upper_arm.L": self.parameters.upper_arm_len,
            "pup.forearm.L": self.parameters.forearm_len,
            "pup.thigh.L": self.parameters.thigh_len,
            "pup.shin.L": self.parameters.shin_len,
            "pup.torso": self.parameters.torso_len,
        }
        parts_by_name = {part.name: part for part in self.parts}
        for object_name, expected_length in expected_lengths.items():
            part = parts_by_name[object_name]
            vertices = self._world_vertices(self.objects[object_name])
            direction = Vector(part.direction).normalized()
            with self.subTest(object_name=object_name):
                self.assertAlmostEqual(
                    self._extent(vertices, direction),
                    expected_length,
                    places=5,
                )


if __name__ == "__main__":
    unittest.main()
