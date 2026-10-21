import tempfile
import unittest
from pathlib import Path

from puppet_pipeline.styling.presets import (
    PresetError,
    StylingPreset,
    validate_preset_filename,
)


def _valid_preset_payload() -> dict:
    return {
        "schema": "styling-preset-v1",
        "fill_mode": "solid",
        "materials": {"head": "skin_light", "torso": "blue"},
        "accessories": [
            {"style": "sneakers", "attach_bone": "foot.L"},
            {"style": "cap", "attach_bone": "head"},
        ],
        "background": "playground",
    }


class StylingPresetParseTests(unittest.TestCase):
    def test_parse_valid_preset(self) -> None:
        preset = StylingPreset.from_dict(_valid_preset_payload())
        self.assertEqual(preset.fill_mode, "solid")
        self.assertEqual(preset.materials["head"], "skin_light")
        self.assertEqual(len(preset.accessories), 2)
        self.assertEqual(preset.background, "playground")

    def test_parse_minimal_preset(self) -> None:
        preset = StylingPreset.from_dict({"schema": "styling-preset-v1"})
        self.assertEqual(preset.fill_mode, "solid")
        self.assertEqual(preset.materials, {})
        self.assertEqual(preset.accessories, [])
        self.assertIsNone(preset.background)

    def test_rejects_wrong_schema(self) -> None:
        for schema in ("styling-v1", "v2", 1, None):
            with self.subTest(schema=schema):
                payload = _valid_preset_payload()
                payload["schema"] = schema
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)

    def test_rejects_invalid_fill_mode(self) -> None:
        payload = _valid_preset_payload()
        payload["fill_mode"] = "shaded"
        with self.assertRaises(PresetError):
            StylingPreset.from_dict(payload)

    def test_rejects_unknown_top_level_key(self) -> None:
        payload = _valid_preset_payload()
        payload["extra"] = True
        with self.assertRaises(PresetError):
            StylingPreset.from_dict(payload)

    def test_rejects_invalid_part_names(self) -> None:
        for part in ("pup.head", "nose", "head.L", ""):
            with self.subTest(part=part):
                payload = _valid_preset_payload()
                payload["materials"] = {part: "blue"}
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)

    def test_rejects_empty_material_value(self) -> None:
        payload = _valid_preset_payload()
        payload["materials"] = {"head": ""}
        with self.assertRaises(PresetError):
            StylingPreset.from_dict(payload)

    def test_rejects_invalid_attach_bone(self) -> None:
        for bone in ("foot", "hand.L", "foot.l", "hips"):
            with self.subTest(bone=bone):
                payload = _valid_preset_payload()
                payload["accessories"] = [{"style": "sneakers", "attach_bone": bone}]
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)

    def test_rejects_malformed_accessory(self) -> None:
        for accessory in (
            {"style": "sneakers"},
            {"attach_bone": "foot.L"},
            {"style": "", "attach_bone": "foot.L"},
            "sneakers",
        ):
            with self.subTest(accessory=accessory):
                payload = _valid_preset_payload()
                payload["accessories"] = [accessory]
                with self.assertRaises(PresetError):
                    StylingPreset.from_dict(payload)


class StylingPresetRoundTripTests(unittest.TestCase):
    def test_dict_round_trip(self) -> None:
        payload = _valid_preset_payload()
        preset = StylingPreset.from_dict(payload)
        expected = {**payload, "schema": "styling-preset-v2", "outline": None}
        self.assertEqual(preset.to_dict(), expected)

    def test_file_round_trip(self) -> None:
        preset = StylingPreset.from_dict(_valid_preset_payload())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "look.json"
            preset.save(path)
            loaded = StylingPreset.load(path)
        self.assertEqual(loaded.to_dict(), preset.to_dict())

    def test_load_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(PresetError):
                StylingPreset.load(path)


class PresetFilenameTests(unittest.TestCase):
    def test_valid_filenames(self) -> None:
        for name in ("look.json", "my-look.json", "look_v2.json", "A.b-1.json"):
            with self.subTest(name=name):
                validate_preset_filename(name)

    def test_invalid_filenames(self) -> None:
        for name in ("my look.json", "look/.json", "../look.json", "look:john.json", ""):
            with self.subTest(name=name):
                with self.assertRaises(PresetError):
                    validate_preset_filename(name)


if __name__ == "__main__":
    unittest.main()
