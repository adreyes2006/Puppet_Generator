import json
import unittest
from types import SimpleNamespace

from puppet_pipeline.common import naming
from puppet_pipeline.common.manifest import ManifestWriter
from puppet_pipeline.common.params import PuppetParameters


PARENTS = {
    "hips": None,
    "spine": "hips",
    "chest": "spine",
    "neck": "chest",
    "head": "neck",
    "shoulder.L": "chest",
    "shoulder.R": "chest",
    "upper_arm.L": "shoulder.L",
    "upper_arm.R": "shoulder.R",
    "forearm.L": "upper_arm.L",
    "forearm.R": "upper_arm.R",
    "hand.L": "forearm.L",
    "hand.R": "forearm.R",
    "thigh.L": "hips",
    "thigh.R": "hips",
    "shin.L": "thigh.L",
    "shin.R": "thigh.R",
    "foot.L": "shin.L",
    "foot.R": "shin.R",
}


class ManifestWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = PuppetParameters(seed=42)
        self.objects = {
            name: SimpleNamespace(data=SimpleNamespace(vertices=range(index + 3)))
            for index, name in enumerate(naming.GEOMETRY_BINDINGS)
        }
        bones = []
        by_name = {}
        for name in naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES:
            parent_name = PARENTS.get(name, "hips")
            bone = SimpleNamespace(
                name=name,
                parent=by_name.get(parent_name),
                use_deform=name in naming.DEFORMING_BONE_NAMES,
            )
            bones.append(bone)
            by_name[name] = bone
        pose_bones = []
        for bone in bones:
            constraints = []
            if bone.name in {"forearm.L", "forearm.R", "shin.L", "shin.R"}:
                side = bone.name[-1]
                arm = bone.name.startswith("forearm")
                constraints.append(
                    SimpleNamespace(
                        type="IK",
                        subtarget=f"{'hand' if arm else 'foot'}_ctrl.{side}",
                        pole_subtarget=f"{'elbow' if arm else 'knee'}_pole.{side}",
                        chain_count=2,
                    )
                )
            elif bone.use_deform and bone.name not in {
                "upper_arm.L",
                "upper_arm.R",
                "thigh.L",
                "thigh.R",
            }:
                constraints.append(SimpleNamespace(type="LIMIT_ROTATION"))
            pose_bones.append(SimpleNamespace(name=bone.name, constraints=constraints))
        self.armature = SimpleNamespace(
            data=SimpleNamespace(bones=bones),
            pose=SimpleNamespace(bones=pose_bones),
        )

    def test_builds_complete_schema_v1_content_in_stable_order(self) -> None:
        manifest = ManifestWriter.build(
            self.parameters,
            self.objects,
            self.armature,
        )

        self.assertEqual(
            list(manifest),
            [
                "schema_version",
                "naming_version",
                "seed",
                "parameters",
                "objects",
                "bones",
                "control_bones",
                "constraints",
            ],
        )
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["naming_version"], naming.NAMING_VERSION)
        self.assertEqual(manifest["seed"], 42)
        self.assertEqual(len(manifest["objects"]), 14)
        self.assertEqual(len(manifest["bones"]), 27)
        self.assertEqual(
            manifest["control_bones"],
            list(naming.CONTROL_BONE_NAMES),
        )
        self.assertEqual(
            [record["name"] for record in manifest["objects"]],
            list(naming.GEOMETRY_BINDINGS),
        )
        self.assertEqual(
            [record["name"] for record in manifest["bones"]],
            list(naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES),
        )

    def test_parameter_fields_and_values_match_schema(self) -> None:
        manifest = ManifestWriter.build(self.parameters, self.objects, self.armature)

        self.assertEqual(
            manifest["parameters"],
            {
                "upper_arm_len": 1.0,
                "forearm_len": 0.9,
                "thigh_len": 1.2,
                "shin_len": 1.1,
                "limb_radius": 0.06,
                "torso_len": 1.4,
                "head_radius": 0.22,
                "hip_width": 0.35,
                "shoulder_width": 0.55,
            },
        )

    def test_object_records_include_binding_and_vertex_count(self) -> None:
        manifest = ManifestWriter.build(self.parameters, self.objects, self.armature)

        for index, record in enumerate(manifest["objects"]):
            with self.subTest(record=record["name"]):
                self.assertEqual(record["bone"], naming.GEOMETRY_BINDINGS[record["name"]])
                self.assertEqual(record["vertex_count"], index + 3)

    def test_serialization_is_byte_deterministic_and_valid_json(self) -> None:
        first = ManifestWriter.serialize(
            ManifestWriter.build(self.parameters, self.objects, self.armature)
        )
        second = ManifestWriter.serialize(
            ManifestWriter.build(self.parameters, self.objects, self.armature)
        )

        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertEqual(json.loads(first), json.loads(second))


if __name__ == "__main__":
    unittest.main()
