import json
import tempfile
import unittest
from pathlib import Path

from puppet_pipeline.common import naming
from puppet_pipeline.common.manifest import ManifestWriter
from puppet_pipeline.common.scene import reset_puppet_scene
from tests.blender.fixtures import build_rig_fixture


class LiveManifestContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "puppet.manifest.json"
        ManifestWriter.write(
            self.path,
            self.fixture.parameters,
            self.fixture.objects,
            self.fixture.armature,
        )
        self.manifest = json.loads(self.path.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        reset_puppet_scene()
        self.temporary_directory.cleanup()

    def test_manifest_objects_match_live_geometry_and_bindings(self) -> None:
        records = {record["name"]: record for record in self.manifest["objects"]}
        self.assertEqual(set(records), set(self.fixture.objects))
        for name, obj in self.fixture.objects.items():
            with self.subTest(obj=name):
                self.assertEqual(records[name]["vertex_count"], len(obj.data.vertices))
                self.assertEqual(records[name]["bone"], naming.GEOMETRY_BINDINGS[name])
                self.assertIsNotNone(obj.vertex_groups.get(records[name]["bone"]))

    def test_manifest_bones_match_live_hierarchy_and_deform_flags(self) -> None:
        records = {record["name"]: record for record in self.manifest["bones"]}
        self.assertEqual(set(records), {bone.name for bone in self.fixture.armature.data.bones})
        for bone in self.fixture.armature.data.bones:
            with self.subTest(bone=bone.name):
                self.assertEqual(records[bone.name]["parent"], bone.parent.name if bone.parent else None)
                self.assertEqual(records[bone.name]["deforms"], bone.use_deform)

    def test_manifest_controls_and_constraints_match_live_rig(self) -> None:
        self.assertEqual(self.manifest["control_bones"], list(naming.CONTROL_BONE_NAMES))
        expected = {
            (pose_bone.name, constraint.type)
            for pose_bone in self.fixture.armature.pose.bones
            for constraint in pose_bone.constraints
            if constraint.type in {"IK", "LIMIT_ROTATION"}
        }
        actual = {
            (record["bone"], record["type"])
            for record in self.manifest["constraints"]
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
