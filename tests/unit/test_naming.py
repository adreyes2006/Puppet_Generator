import unittest

from puppet_pipeline.common import naming


class NamingConstantsTests(unittest.TestCase):
    def test_contract_version_and_scene_names(self) -> None:
        self.assertEqual(naming.NAMING_VERSION, 1)
        self.assertEqual(naming.ROOT_COLLECTION_NAME, "PUPPET")
        self.assertEqual(naming.GEOMETRY_COLLECTION_NAME, "PUPPET.GEOMETRY")
        self.assertEqual(naming.RIG_COLLECTION_NAME, "PUPPET.RIG")
        self.assertEqual(naming.ARMATURE_OBJECT_NAME, "rig")
        self.assertEqual(naming.ARMATURE_DATA_NAME, "rig.data")

    def test_geometry_bindings_are_complete(self) -> None:
        self.assertEqual(
            naming.GEOMETRY_BINDINGS,
            {
                "pup.head": "head",
                "pup.torso": "spine",
                "pup.upper_arm.L": "upper_arm.L",
                "pup.upper_arm.R": "upper_arm.R",
                "pup.forearm.L": "forearm.L",
                "pup.forearm.R": "forearm.R",
                "pup.hand.L": "hand.L",
                "pup.hand.R": "hand.R",
                "pup.thigh.L": "thigh.L",
                "pup.thigh.R": "thigh.R",
                "pup.shin.L": "shin.L",
                "pup.shin.R": "shin.R",
                "pup.foot.L": "foot.L",
                "pup.foot.R": "foot.R",
            },
        )

    def test_deforming_bone_names_are_complete(self) -> None:
        self.assertEqual(
            set(naming.DEFORMING_BONE_NAMES),
            {
                "hips",
                "spine",
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
                "thigh.L",
                "thigh.R",
                "shin.L",
                "shin.R",
                "foot.L",
                "foot.R",
            },
        )

    def test_control_bone_names_are_complete(self) -> None:
        self.assertEqual(
            set(naming.CONTROL_BONE_NAMES),
            {
                "hand_ctrl.L",
                "hand_ctrl.R",
                "foot_ctrl.L",
                "foot_ctrl.R",
                "elbow_pole.L",
                "elbow_pole.R",
                "knee_pole.L",
                "knee_pole.R",
            },
        )

    def test_animation_names_are_reserved(self) -> None:
        self.assertEqual(naming.RESERVED_BONE_PREFIX, "anim_")
        self.assertEqual(naming.ANIMATION_COLLECTION_NAME, "PUPPET.ANIMATION")
        self.assertTrue(naming.is_reserved_name("anim_hand_space"))
        self.assertTrue(naming.is_reserved_name("PUPPET.ANIMATION"))
        self.assertFalse(naming.is_reserved_name("hand_ctrl.L"))


class NamingRuleTests(unittest.TestCase):
    def test_bilateral_name_appends_terminal_side_suffix(self) -> None:
        self.assertEqual(naming.bilateral_name("upper_arm", "L"), "upper_arm.L")
        self.assertEqual(naming.bilateral_name("upper_arm", "R"), "upper_arm.R")

    def test_bilateral_name_rejects_invalid_side(self) -> None:
        for side in ("l", "r", "LEFT", "", "X"):
            with self.subTest(side=side):
                with self.assertRaises(naming.NamingError):
                    naming.bilateral_name("upper_arm", side)

    def test_bilateral_name_rejects_non_snake_case_base(self) -> None:
        for base in ("UpperArm", "upper-arm", "upper arm", "upper_arm.L", ""):
            with self.subTest(base=base):
                with self.assertRaises(naming.NamingError):
                    naming.bilateral_name(base, "L")

    def test_numeric_suffix_detection_rejects_blender_duplicates(self) -> None:
        for generated_name in ("pup.head.001", "forearm.L.002", "rig.123"):
            with self.subTest(generated_name=generated_name):
                self.assertTrue(naming.has_blender_numeric_suffix(generated_name))
                with self.assertRaises(naming.NamingError):
                    naming.validate_generated_name(generated_name)

    def test_valid_contract_names_are_accepted(self) -> None:
        for generated_name in (
            "pup.head",
            "pup.upper_arm.L",
            "hips",
            "forearm.R",
            "hand_ctrl.L",
            "PUPPET",
            "PUPPET.GEOMETRY",
            "rig",
            "rig.data",
        ):
            with self.subTest(generated_name=generated_name):
                self.assertFalse(naming.has_blender_numeric_suffix(generated_name))
                naming.validate_generated_name(generated_name)

    def test_reserved_names_are_rejected_for_generation_and_rigging(self) -> None:
        for generated_name in ("anim_hand_space", "PUPPET.ANIMATION"):
            with self.subTest(generated_name=generated_name):
                with self.assertRaises(naming.NamingError):
                    naming.validate_generated_name(generated_name)


if __name__ == "__main__":
    unittest.main()
