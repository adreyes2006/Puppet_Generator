import unittest

from puppet_pipeline.styling.manifest import (
    STYLING_SCHEMA,
    StylingManifestError,
    StylingManifestWriter,
    StylingState,
)


def _state() -> StylingState:
    return StylingState(
        fill_mode="solid",
        materials={"torso": "blue"},
        accessories=[{"name": "acc.shoe.sneakers.L", "style": "sneakers", "attach_bone": "foot.L"}],
        background="playground",
        outline={"enabled": True, "thickness": 0.015, "color": "#0d0d0d"},
        render={"engine": "BLENDER_EEVEE_NEXT", "resolution_x": 1920, "resolution_y": 1080},
        preview_files=["material-blue.png"],
    )


class ManifestV2Tests(unittest.TestCase):
    def test_build_emits_v2_with_outline_and_render(self) -> None:
        manifest = StylingManifestWriter.build(_state(), "src.json", "5.2.2")
        self.assertEqual(manifest["schema"], "styling-v2")
        self.assertEqual(manifest["outline"]["color"], "#0d0d0d")
        self.assertEqual(manifest["render"]["engine"], "BLENDER_EEVEE_NEXT")
        self.assertEqual(manifest["render"]["resolution_x"], 1920)

    def test_null_outline_and_render(self) -> None:
        state = StylingState(materials={"torso": "blue"})
        manifest = StylingManifestWriter.build(state, "src.json", "5.2.2")
        self.assertIsNone(manifest["outline"])
        self.assertIsNone(manifest["render"])

    def test_deterministic_serialization(self) -> None:
        manifest = StylingManifestWriter.build(_state(), "src.json", "5.2.2")
        self.assertEqual(
            StylingManifestWriter.serialize(manifest),
            StylingManifestWriter.serialize(
                StylingManifestWriter.build(_state(), "src.json", "5.2.2")
            ),
        )

    def test_read_accepts_v1(self) -> None:
        v1 = {
            "schema": "styling-v1",
            "source_manifest": "src.json",
            "blender_version": "4.2.3",
            "fill_mode": "solid",
            "materials": {},
            "accessories": [],
            "background": None,
            "preview_files": [],
        }
        read = StylingManifestWriter.read(v1)
        self.assertIsNone(read["outline"])
        self.assertIsNone(read["render"])

    def test_read_accepts_v2(self) -> None:
        manifest = StylingManifestWriter.build(_state(), "src.json", "5.2.2")
        self.assertEqual(StylingManifestWriter.read(manifest), manifest)

    def test_read_rejects_unknown_schema(self) -> None:
        with self.assertRaises(StylingManifestError):
            StylingManifestWriter.read({"schema": "styling-v99"})


if __name__ == "__main__":
    unittest.main()
