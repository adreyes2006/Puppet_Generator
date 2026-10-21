import unittest

from puppet_pipeline.styling import naming as styling_naming


class StylingNamingConstantsTests(unittest.TestCase):
    def test_contract_version(self) -> None:
        self.assertEqual(styling_naming.STYLING_NAMING_VERSION, "1.1")

    def test_style_collection_names(self) -> None:
        self.assertEqual(styling_naming.STYLE_COLLECTION_NAME, "PUPPET.STYLE")
        self.assertEqual(
            styling_naming.ACCESSORY_COLLECTION_NAME,
            "PUPPET.STYLE.ACCESSORIES",
        )
        self.assertEqual(
            styling_naming.BACKGROUND_COLLECTION_NAME,
            "PUPPET.STYLE.BACKGROUND",
        )

    def test_accessory_name_uses_acc_prefix(self) -> None:
        self.assertEqual(
            styling_naming.accessory_name("shoe", "sneakers"),
            "acc.shoe.sneakers",
        )
        self.assertEqual(
            styling_naming.accessory_name("shoe", "sneakers", side="L"),
            "acc.shoe.sneakers.L",
        )
        self.assertEqual(styling_naming.accessory_name("hat", "cap"), "acc.hat.cap")

    def test_accessory_name_rejects_invalid_side(self) -> None:
        for side in ("l", "LEFT", "X", ""):
            with self.subTest(side=side):
                with self.assertRaises(styling_naming.StylingNamingError):
                    styling_naming.accessory_name("shoe", "sneakers", side=side)

    def test_accessory_name_rejects_invalid_kind_or_style(self) -> None:
        for kind, style in (("Shoe", "sneakers"), ("shoe", "Sneakers"), ("", "cap"), ("hat", "")):
            with self.subTest(kind=kind, style=style):
                with self.assertRaises(styling_naming.StylingNamingError):
                    styling_naming.accessory_name(kind, style)

    def test_background_name_uses_bg_prefix(self) -> None:
        self.assertEqual(styling_naming.background_name("ground"), "bg.ground")
        self.assertEqual(styling_naming.prop_name("slide"), "bg.prop.slide")

    def test_background_name_rejects_invalid_element(self) -> None:
        for element in ("Ground", "ground-floor", "", "prop."):
            with self.subTest(element=element):
                with self.assertRaises(styling_naming.StylingNamingError):
                    styling_naming.background_name(element)

    def test_material_name_uses_mat_prefix(self) -> None:
        self.assertEqual(styling_naming.material_name("blue"), "mat.blue")
        self.assertEqual(styling_naming.material_name("skin_light"), "mat.skin_light")

    def test_material_name_rejects_invalid_preset(self) -> None:
        for preset in ("Blue", "skin-light", "", "mat.blue"):
            with self.subTest(preset=preset):
                with self.assertRaises(styling_naming.StylingNamingError):
                    styling_naming.material_name(preset)

    def test_styling_names_are_not_reserved_animation_names(self) -> None:
        for name in (
            styling_naming.STYLE_COLLECTION_NAME,
            styling_naming.accessory_name("hat", "cap"),
            styling_naming.background_name("ground"),
            styling_naming.material_name("blue"),
        ):
            with self.subTest(name=name):
                self.assertFalse(name.startswith("anim_"))
                self.assertNotEqual(name, "PUPPET.ANIMATION")

    def test_styling_names_have_no_numeric_suffix(self) -> None:
        for name in (
            "PUPPET.STYLE",
            "PUPPET.STYLE.ACCESSORIES",
            "PUPPET.STYLE.BACKGROUND",
            "acc.shoe.sneakers.L",
            "bg.prop.swing",
            "mat.metallic",
        ):
            with self.subTest(name=name):
                self.assertFalse(styling_naming.has_numeric_suffix(name))


if __name__ == "__main__":
    unittest.main()
