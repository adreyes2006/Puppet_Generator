import unittest

import bpy

from puppet_pipeline.styling.materials import MaterialApplier
from puppet_pipeline.styling import naming as styling_naming
from tests.blender.fixtures import build_rig_fixture


class MaterialApplierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def tearDown(self) -> None:
        for material in list(bpy.data.materials):
            if material.name.startswith("mat."):
                bpy.data.materials.remove(material)

    def _principled(self, material):
        return next(
            node
            for node in material.node_tree.nodes
            if node.type == "BSDF_PRINCIPLED"
        )

    def test_apply_assigns_named_material_to_object(self) -> None:
        obj = self.fixture.objects["pup.torso"]
        MaterialApplier.apply(obj, "blue")
        self.assertEqual(len(obj.data.materials), 1)
        material = obj.data.materials[0]
        self.assertEqual(material.name, "mat.blue")
        self.assertTrue(material.use_nodes)

    def test_apply_sets_principled_inputs(self) -> None:
        obj = self.fixture.objects["pup.head"]
        MaterialApplier.apply(obj, "metallic")
        node = self._principled(obj.data.materials[0])
        preset = __import__(
            "puppet_pipeline.styling.materials", fromlist=["MATERIAL_CATALOG"]
        ).MATERIAL_CATALOG["metallic"]
        self.assertAlmostEqual(node.inputs["Metallic"].default_value, preset.metallic)
        self.assertAlmostEqual(node.inputs["Roughness"].default_value, preset.roughness)
        base = node.inputs["Base Color"].default_value
        for channel, expected in zip(base[:3], preset.base_color[:3]):
            self.assertAlmostEqual(channel, expected, places=4)

    def test_reapply_reuses_datablock_no_duplicate(self) -> None:
        MaterialApplier.apply(self.fixture.objects["pup.torso"], "blue")
        MaterialApplier.apply(self.fixture.objects["pup.head"], "blue")
        mats = [m for m in bpy.data.materials if m.name.startswith("mat.blue")]
        self.assertEqual(len(mats), 1)
        self.assertIs(
            self.fixture.objects["pup.torso"].data.materials[0],
            self.fixture.objects["pup.head"].data.materials[0],
        )

    def test_reapply_replaces_existing_material(self) -> None:
        obj = self.fixture.objects["pup.torso"]
        MaterialApplier.apply(obj, "blue")
        MaterialApplier.apply(obj, "red")
        self.assertEqual(len(obj.data.materials), 1)
        self.assertEqual(obj.data.materials[0].name, "mat.red")

    def test_apply_rejects_unknown_preset(self) -> None:
        with self.assertRaises(ValueError):
            MaterialApplier.apply(self.fixture.objects["pup.torso"], "not_a_preset")

    def test_glowing_preset_sets_emission(self) -> None:
        MaterialApplier.apply(self.fixture.objects["pup.head"], "glow_cyan")
        node = self._principled(self.fixture.objects["pup.head"].data.materials[0])
        emission_strength = node.inputs["Emission Strength"].default_value
        self.assertGreater(emission_strength, 0.0)


if __name__ == "__main__":
    unittest.main()
