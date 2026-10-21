import tempfile
import unittest
from pathlib import Path

from puppet_pipeline.styling.presets import PresetError, StylingPreset


def _v1_payload() -> dict:
    return {
        "schema": "styling-preset-v1",
        "fill_mode": "solid",
        "materials": {"torso": "blue"},
        "accessories": [],
        "background": None,
    }


class V1CompatibilityTests(unittest.TestCase):
    def test_v1_loads_with_no_outline(self) -> None:
        preset = StylingPreset.from_dict(_v1_payload())
        self.assertIsNone(preset.outline)
        self.assertEqual(preset.materials["torso"], "blue")

    def test_v1_save_emits_v2(self) -> None:
        preset = StylingPreset.from_dict(_v1_payload())
        self.assertEqual(preset.to_dict()["schema"], "styling-preset-v2")
        self.assertIsNone(preset.to_dict()["outline"])


class V2OutlineTests(unittest.TestCase):
    def test_v2_round_trip(self) -> None:
        payload = {
            "schema": "styling-preset-v2",
            "fill_mode": "solid",
            "materials": {},
            "accessories": [],
            "background": None,
            "outline": {"enabled": True, "thickness": 0.05, "color": "#ff0000"},
        }
        preset = StylingPreset.from_dict(payload)
        self.assertEqual(preset.to_dict(), payload)

    def test_null_fields_preserved(self) -> None:
        payload = {
            "schema": "styling-preset-v2",
            "fill_mode": "solid",
            "outline": {"enabled": True, "thickness": None, "color": "red"},
        }
        preset = StylingPreset.from_dict(payload)
        self.assertTrue(preset.outline.enabled)
        self.assertIsNone(preset.outline.thickness)
        self.assertEqual(preset.outline.color, "#d32f2f")
        self.assertEqual(preset.to_dict()["outline"]["color"], "#d32f2f")

    def test_unknown_outline_keys_rejected(self) -> None:
        payload = {
            "schema": "styling-preset-v2",
            "fill_mode": "solid",
            "outline": {"enabled": True, "bogus": 1},
        }
        with self.assertRaises(PresetError):
            StylingPreset.from_dict(payload)

    def test_invalid_color_rejected(self) -> None:
        for color in ("chartreuse", "#12345", 42):
            with self.subTest(color=color):
                payload = {
                    "schema": "styling-preset-v2",
                    "fill_mode": "solid",
                    "outline": {"enabled": True, "color": color},
                }
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)

    def test_invalid_thickness_rejected(self) -> None:
        for thickness in (0, -1, "fat"):
            with self.subTest(thickness=thickness):
                payload = {
                    "schema": "styling-preset-v2",
                    "fill_mode": "solid",
                    "outline": {"enabled": True, "thickness": thickness},
                }
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)

    def test_enabled_must_be_bool(self) -> None:
        payload = {
            "schema": "styling-preset-v2",
            "fill_mode": "solid",
            "outline": {"enabled": "yes"},
        }
        with self.assertRaises(PresetError):
            StylingPreset.from_dict(payload)

    def test_file_round_trip_v2(self) -> None:
        payload = {
            "schema": "styling-preset-v2",
            "fill_mode": "solid",
            "materials": {"head": "skin_light"},
            "accessories": [],
            "background": "kitchen",
            "outline": {"enabled": True, "thickness": 0.03, "color": "#101010"},
        }
        preset = StylingPreset.from_dict(payload)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "toon.json"
            preset.save(path)
            loaded = StylingPreset.load(path)
        self.assertEqual(loaded.to_dict(), preset.to_dict())


if __name__ == "__main__":
    unittest.main()
