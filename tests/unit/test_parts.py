import math
import unittest

from puppet_pipeline.common.naming import GEOMETRY_BINDINGS
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.generation.parts import PartSpec, build_part_specs


class CanonicalPartTests(unittest.TestCase):
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
        self.parts = build_part_specs(self.parameters)
        self.by_name = {part.name: part for part in self.parts}

    def test_returns_exactly_fourteen_unique_part_specs(self) -> None:
        self.assertEqual(len(self.parts), 14)
        self.assertTrue(all(isinstance(part, PartSpec) for part in self.parts))
        self.assertEqual(len(self.by_name), 14)
        self.assertEqual(set(self.by_name), set(GEOMETRY_BINDINGS))

    def test_each_part_uses_its_contract_bone(self) -> None:
        for object_name, bone_name in GEOMETRY_BINDINGS.items():
            with self.subTest(object_name=object_name):
                self.assertEqual(self.by_name[object_name].bone_name, bone_name)

    def test_limb_lengths_map_directly_from_parameters(self) -> None:
        expected_lengths = {
            "upper_arm": self.parameters.upper_arm_len,
            "forearm": self.parameters.forearm_len,
            "thigh": self.parameters.thigh_len,
            "shin": self.parameters.shin_len,
        }
        for base_name, expected_length in expected_lengths.items():
            for side in ("L", "R"):
                object_name = f"pup.{base_name}.{side}"
                with self.subTest(object_name=object_name):
                    self.assertEqual(self.by_name[object_name].length, expected_length)

    def test_limb_thickness_maps_to_all_primary_limbs(self) -> None:
        for base_name in ("upper_arm", "forearm", "thigh", "shin"):
            for side in ("L", "R"):
                object_name = f"pup.{base_name}.{side}"
                with self.subTest(object_name=object_name):
                    self.assertEqual(
                        self.by_name[object_name].radius,
                        self.parameters.limb_radius,
                    )

    def test_torso_and_head_dimensions_map_from_parameters(self) -> None:
        self.assertEqual(self.by_name["pup.torso"].length, self.parameters.torso_len)
        self.assertEqual(self.by_name["pup.head"].radius, self.parameters.head_radius)
        self.assertEqual(
            self.by_name["pup.head"].length,
            self.parameters.head_radius * 2,
        )

    def test_bilateral_parts_are_mirrored_across_x_zero(self) -> None:
        for base_name in (
            "upper_arm",
            "forearm",
            "hand",
            "thigh",
            "shin",
            "foot",
        ):
            left = self.by_name[f"pup.{base_name}.L"]
            right = self.by_name[f"pup.{base_name}.R"]
            with self.subTest(base_name=base_name):
                self.assertAlmostEqual(left.origin[0], -right.origin[0])
                self.assertAlmostEqual(left.origin[1], right.origin[1])
                self.assertAlmostEqual(left.origin[2], right.origin[2])
                self.assertAlmostEqual(left.direction[0], -right.direction[0])
                self.assertAlmostEqual(left.direction[1], right.direction[1])
                self.assertAlmostEqual(left.direction[2], right.direction[2])
                self.assertEqual(left.length, right.length)
                self.assertEqual(left.radius, right.radius)

    def test_all_parts_lie_in_xz_plane_with_unit_directions(self) -> None:
        for part in self.parts:
            with self.subTest(part=part.name):
                self.assertEqual(len(part.origin), 3)
                self.assertEqual(len(part.direction), 3)
                self.assertAlmostEqual(part.origin[1], 0.0)
                self.assertAlmostEqual(part.direction[1], 0.0)
                magnitude = math.sqrt(sum(component**2 for component in part.direction))
                self.assertAlmostEqual(magnitude, 1.0)

    def test_same_parameters_produce_equal_ordered_records(self) -> None:
        self.assertEqual(self.parts, build_part_specs(self.parameters))
        self.assertEqual(
            tuple(part.name for part in self.parts),
            tuple(GEOMETRY_BINDINGS),
        )


if __name__ == "__main__":
    unittest.main()
