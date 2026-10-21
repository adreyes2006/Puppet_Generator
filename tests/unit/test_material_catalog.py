import math
import unittest

from puppet_pipeline.styling.materials import MATERIAL_CATALOG, MaterialPreset


class MaterialPresetTests(unittest.TestCase):
    def test_preset_is_frozen_dataclass(self) -> None:
        preset = next(iter(MATERIAL_CATALOG.values()))
        self.assertIsInstance(preset, MaterialPreset)
        with self.assertRaises(AttributeError):
            preset.name = "other"

    def test_catalog_has_at_least_ten_presets(self) -> None:
        self.assertGreaterEqual(len(MATERIAL_CATALOG), 10)

    def test_catalog_names_are_unique_snake_case(self) -> None:
        names = list(MATERIAL_CATALOG)
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(name=name):
                self.assertRegex(name, r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
                self.assertIs(MATERIAL_CATALOG[name].name, name)

    def test_all_channels_are_finite_and_in_range(self) -> None:
        for name, preset in MATERIAL_CATALOG.items():
            with self.subTest(name=name):
                channels = (
                    *preset.base_color,
                    *preset.emission_color,
                    preset.roughness,
                    preset.metallic,
                    preset.emission_strength,
                )
                for channel in channels:
                    self.assertTrue(math.isfinite(channel), f"non-finite channel in {name}")
                for channel in (*preset.base_color, *preset.emission_color):
                    self.assertGreaterEqual(channel, 0.0)
                    self.assertLessEqual(channel, 1.0)
                self.assertGreaterEqual(preset.roughness, 0.0)
                self.assertLessEqual(preset.roughness, 1.0)
                self.assertGreaterEqual(preset.metallic, 0.0)
                self.assertLessEqual(preset.metallic, 1.0)
                self.assertGreaterEqual(preset.emission_strength, 0.0)

    def test_fill_mode_is_valid(self) -> None:
        for name, preset in MATERIAL_CATALOG.items():
            with self.subTest(name=name):
                self.assertIn(preset.fill_mode, ("solid", "outline"))

    def test_catalog_covers_required_families(self) -> None:
        names = set(MATERIAL_CATALOG)
        self.assertTrue(any("skin" in name for name in names), "needs a skin tone preset")
        self.assertTrue(any("metal" in name for name in names), "needs a metallic preset")
        self.assertTrue(any("glow" in name for name in names), "needs a glowing preset")
        self.assertIn("blue", names)
        self.assertIn("red", names)

    def test_glowing_preset_has_nonzero_emission(self) -> None:
        glowing = [p for p in MATERIAL_CATALOG.values() if "glow" in p.name]
        self.assertTrue(glowing, "no glowing preset found")
        for preset in glowing:
            with self.subTest(name=preset.name):
                self.assertGreater(preset.emission_strength, 0.0)


if __name__ == "__main__":
    unittest.main()
