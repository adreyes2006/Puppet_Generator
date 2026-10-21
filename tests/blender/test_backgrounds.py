import unittest

import bpy

from puppet_pipeline.styling import naming as styling_naming
from puppet_pipeline.styling.backgrounds import (
    BACKGROUND_CATALOG,
    BackgroundBuilder,
)
from tests.blender.fixtures import build_rig_fixture


def _bg_objects():
    return [o for o in bpy.data.objects if o.name.startswith("bg.")]


class BackgroundCatalogTests(unittest.TestCase):
    def test_five_scenarios_exist(self) -> None:
        for scenario in ("kitchen", "playground", "office", "room", "bathroom"):
            self.assertIn(scenario, BACKGROUND_CATALOG)

    def test_each_scenario_has_at_least_two_props(self) -> None:
        for name, spec in BACKGROUND_CATALOG.items():
            with self.subTest(scenario=name):
                self.assertGreaterEqual(len(spec.props), 2)

    def test_props_are_planar_specs(self) -> None:
        for name, spec in BACKGROUND_CATALOG.items():
            with self.subTest(scenario=name):
                for prop in spec.props:
                    self.assertGreater(prop.scale[0], 0.0)
                    self.assertGreater(prop.scale[1], 0.0)


class BackgroundBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()

    def tearDown(self) -> None:
        BackgroundBuilder.clear()

    def test_build_creates_bg_objects_in_background_collection(self) -> None:
        BackgroundBuilder.build("playground")
        objects = _bg_objects()
        self.assertGreaterEqual(len(objects), 4)
        for obj in objects:
            self.assertEqual(
                [c.name for c in obj.users_collection],
                [styling_naming.BACKGROUND_COLLECTION_NAME],
            )

    def test_background_is_planar_at_positive_y(self) -> None:
        spec = BACKGROUND_CATALOG["kitchen"]
        BackgroundBuilder.build("kitchen")
        for obj in _bg_objects():
            with self.subTest(obj=obj.name):
                ys = [
                    (obj.matrix_world @ v.co).y for v in obj.data.vertices
                ]
                self.assertAlmostEqual(max(ys) - min(ys), 0.0, places=6)
                self.assertGreater(ys[0], spec.depth_y - 0.1)
                self.assertLessEqual(ys[0], spec.depth_y + 1e-6)

    def test_all_objects_share_depth_plane(self) -> None:
        spec = BACKGROUND_CATALOG["office"]
        BackgroundBuilder.build("office")
        ys = [
            (o.matrix_world @ v.co).y
            for o in _bg_objects()
            for v in o.data.vertices
        ]
        self.assertGreater(min(ys), spec.depth_y - 0.1)
        self.assertLessEqual(max(ys), spec.depth_y + 1e-6)

    def test_objects_have_flat_materials(self) -> None:
        BackgroundBuilder.build("room")
        for obj in _bg_objects():
            with self.subTest(obj=obj.name):
                self.assertGreaterEqual(len(obj.data.materials), 1)
                for material in obj.data.materials:
                    self.assertTrue(material.name.startswith("mat."))

    def test_props_have_multiple_tones(self) -> None:
        BackgroundBuilder.build("playground")
        for obj in _bg_objects():
            if not obj.name.startswith("bg.prop."):
                continue
            with self.subTest(obj=obj.name):
                self.assertGreaterEqual(len(obj.data.materials), 2)
                self.assertGreaterEqual(len(obj.data.polygons), 2)

    def test_every_catalog_prop_enriched(self) -> None:
        for scenario_name, spec in BACKGROUND_CATALOG.items():
            for prop in spec.props:
                with self.subTest(scenario=scenario_name, prop=prop.name):
                    self.assertGreaterEqual(
                        len(prop.sub_props) + 1,
                        2,
                        "prop must compose at least 2 primitives",
                    )

    def test_clear_removes_all_bg_objects(self) -> None:
        BackgroundBuilder.build("playground")
        BackgroundBuilder.clear()
        self.assertEqual(_bg_objects(), [])

    def test_rebuild_replaces_previous_scenario(self) -> None:
        BackgroundBuilder.build("kitchen")
        self.assertIsNotNone(bpy.data.objects.get("bg.prop.fridge"))
        BackgroundBuilder.build("bathroom")
        self.assertIsNone(bpy.data.objects.get("bg.prop.fridge"))
        self.assertIsNotNone(bpy.data.objects.get("bg.prop.toilet"))
        self.assertTrue(_bg_objects())

    def test_unknown_scenario_raises(self) -> None:
        with self.assertRaises(ValueError):
            BackgroundBuilder.build("volcano")


if __name__ == "__main__":
    unittest.main()
