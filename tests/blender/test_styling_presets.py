import tempfile
import unittest
from pathlib import Path

import bpy

from puppet_pipeline.common import naming
from puppet_pipeline.styling import naming as styling_naming
from puppet_pipeline.styling.manifest import (
    StylingManifestWriter,
    StylingState,
)
from puppet_pipeline.styling.presets import StylingPreset, reset_styling
from tests.blender.fixtures import build_rig_fixture

_VERSION = ".".join(map(str, bpy.app.version))


def _styled(state: StylingState):
    preset = StylingPreset(
        fill_mode=state.fill_mode,
        materials={
            part.removeprefix("pup."): v for part, v in state.materials.items()
        },
        accessories=[
            {"style": e["style"], "attach_bone": e["attach_bone"]}
            for e in state.accessories
        ],
        background=state.background,
    )
    return preset.apply()


def _style_all(tmp: Path):
    from puppet_pipeline.styling.accessories import AccessoryBuilder
    from puppet_pipeline.styling.backgrounds import BackgroundBuilder
    from puppet_pipeline.styling.materials import MaterialApplier

    for part, preset_name in {"torso": "blue", "head": "red"}.items():
        MaterialApplier.apply(bpy.data.objects[f"pup.{part}"], preset_name)
    MaterialApplier.set_fill_mode("outline", 0.1)
    accessories = AccessoryBuilder.build("sneakers", limb_thickness=0.1)
    accessories += AccessoryBuilder.build("cap", limb_thickness=0.1)
    background = BackgroundBuilder.build("kitchen")
    state = StylingState(
        fill_mode="outline",
        materials={"torso": "blue", "head": "red"},
        accessories=accessories,
        background=background,
    )
    manifest_path = tmp / "puppet.styling.json"
    StylingManifestWriter.write(
        manifest_path, state, "source.manifest.json", _VERSION
    )
    preset_path = tmp / "style.preset.json"
    StylingPreset(
        fill_mode="outline",
        materials={"torso": "blue", "head": "red"},
        accessories=[
            {"style": e["style"], "attach_bone": e["attach_bone"]}
            for e in accessories
        ],
        background=background,
    ).save(preset_path)
    return manifest_path, preset_path


class PresetRoundTripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        reset_styling()
        self.tmp.cleanup()

    def test_reset_then_reapply_gives_identical_manifest(self) -> None:
        manifest_path, preset_path = _style_all(self.dir)
        original_bytes = manifest_path.read_bytes()

        import json

        payload = json.loads(preset_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "styling-preset-v2")

        reset_styling()
        self.assertEqual([o for o in bpy.data.objects if o.name.startswith("acc.")], [])
        self.assertEqual([o for o in bpy.data.objects if o.name.startswith("bg.")], [])

        preset = StylingPreset.load(preset_path)
        state = preset.apply()
        restored = self.dir / "restored.styling.json"
        StylingManifestWriter.write(
            restored, state, "source.manifest.json", _VERSION
        )
        self.assertEqual(restored.read_bytes(), original_bytes)


class ResetCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.vertex_counts = {
            name: len(bpy.data.objects[name].data.vertices)
            for name in naming.GEOMETRY_BINDINGS
        }
        self.group_counts = {
            name: len(bpy.data.objects[name].vertex_groups)
            for name in naming.GEOMETRY_BINDINGS
        }

    def tearDown(self) -> None:
        reset_styling()

    def test_reset_restores_pre_styling_state(self) -> None:
        _style_all(Path(tempfile.mkdtemp()))
        reset_styling()

        self.assertEqual(
            [o for o in bpy.data.objects if o.name.startswith(("acc.", "bg."))], []
        )
        self.assertEqual(
            [m for m in bpy.data.materials if m.name.startswith("mat.")], []
        )
        for name in naming.GEOMETRY_BINDINGS:
            obj = bpy.data.objects[name]
            with self.subTest(part=name):
                self.assertNotIn("WIREFRAME", [m.type for m in obj.modifiers])
                self.assertEqual(len(obj.data.vertices), self.vertex_counts[name])
                self.assertEqual(len(obj.vertex_groups), self.group_counts[name])
        self.assertIsNone(
            bpy.data.collections.get(styling_naming.STYLE_COLLECTION_NAME)
        )
        self.assertIsNone(
            bpy.data.collections.get(styling_naming.ACCESSORY_COLLECTION_NAME)
        )
        self.assertIsNone(
            bpy.data.collections.get(styling_naming.BACKGROUND_COLLECTION_NAME)
        )


if __name__ == "__main__":
    unittest.main()
