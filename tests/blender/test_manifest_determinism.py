import tempfile
import unittest
from pathlib import Path

import generate_puppet
from puppet_pipeline.common.scene import reset_puppet_scene


class ManifestDeterminismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        reset_puppet_scene()
        self.temporary_directory.cleanup()

    def _generate(self, stem: str, *arguments: str) -> tuple[Path, Path]:
        blend = self.directory / f"{stem}.blend"
        manifest = self.directory / f"{stem}.json"
        status = generate_puppet.main(
            [
                "blender",
                "--background",
                "--",
                *arguments,
                "--output",
                str(blend),
                "--manifest",
                str(manifest),
            ]
        )
        self.assertEqual(status, 0)
        self.assertTrue(blend.is_file())
        self.assertTrue(manifest.is_file())
        return blend, manifest

    def test_identical_parameters_and_seed_produce_identical_manifest_bytes(self) -> None:
        _, first = self._generate("first", "--seed", "42")
        _, second = self._generate("second", "--seed", "42")

        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_changed_dimensions_and_seed_are_recorded(self) -> None:
        _, default = self._generate("default")
        _, custom = self._generate(
            "custom",
            "--upper-arm-length",
            "1.5",
            "--limb-thickness",
            "0.1",
            "--seed",
            "42",
        )

        self.assertNotEqual(default.read_bytes(), custom.read_bytes())
        custom_text = custom.read_text(encoding="utf-8")
        self.assertIn('"upper_arm_len": 1.5', custom_text)
        self.assertIn('"limb_radius": 0.1', custom_text)
        self.assertIn('"seed": 42', custom_text)


if __name__ == "__main__":
    unittest.main()
