from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters

_PARAMETER_FIELDS = (
    "upper_arm_len",
    "forearm_len",
    "thigh_len",
    "shin_len",
    "limb_radius",
    "torso_len",
    "head_radius",
    "hip_width",
    "shoulder_width",
)


class ManifestWriter:
    @staticmethod
    def build(
        parameters: PuppetParameters,
        objects: dict[str, Any],
        armature: Any,
    ) -> dict[str, Any]:
        parameters.validate()
        missing_objects = set(naming.GEOMETRY_BINDINGS) - set(objects)
        if missing_objects:
            raise ValueError(
                f"Manifest cannot omit geometry: {sorted(missing_objects)}"
            )

        pose_bones = {bone.name: bone for bone in armature.pose.bones}
        constraints = []
        ik_chain_counts = {}
        for bone_name in naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES:
            pose_bone = pose_bones.get(bone_name)
            if pose_bone is None:
                raise ValueError(f"Manifest cannot omit pose bone: {bone_name}")
            for constraint in pose_bone.constraints:
                if constraint.type == "IK":
                    constraints.append(
                        {
                            "bone": bone_name,
                            "type": "IK",
                            "target": constraint.subtarget,
                            "pole": constraint.pole_subtarget,
                            "chain_count": constraint.chain_count,
                        }
                    )
                    ik_chain_counts[bone_name] = constraint.chain_count
                elif constraint.type == "LIMIT_ROTATION":
                    constraints.append(
                        {
                            "bone": bone_name,
                            "type": "LIMIT_ROTATION",
                        }
                    )

        bones_by_name = {bone.name: bone for bone in armature.data.bones}
        ordered_bones = naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES
        missing_bones = set(ordered_bones) - set(bones_by_name)
        if missing_bones:
            raise ValueError(f"Manifest cannot omit bones: {sorted(missing_bones)}")

        return {
            "schema_version": 1,
            "naming_version": naming.NAMING_VERSION,
            "seed": parameters.seed,
            "parameters": {
                field_name: getattr(parameters, field_name)
                for field_name in _PARAMETER_FIELDS
            },
            "objects": [
                {
                    "name": object_name,
                    "bone": bone_name,
                    "vertex_count": len(objects[object_name].data.vertices),
                }
                for object_name, bone_name in naming.GEOMETRY_BINDINGS.items()
            ],
            "bones": [
                {
                    "name": bone_name,
                    "parent": (
                        bones_by_name[bone_name].parent.name
                        if bones_by_name[bone_name].parent
                        else None
                    ),
                    "deforms": bones_by_name[bone_name].use_deform,
                    "ik_chain": ik_chain_counts.get(bone_name, 0),
                }
                for bone_name in ordered_bones
            ],
            "control_bones": list(naming.CONTROL_BONE_NAMES),
            "constraints": constraints,
        }

    @staticmethod
    def serialize(manifest: dict[str, Any]) -> bytes:
        return (
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
                separators=(",", ": "),
            )
            + "\n"
        ).encode("utf-8")

    @classmethod
    def write(
        cls,
        path: Path,
        parameters: PuppetParameters,
        objects: dict[str, Any],
        armature: Any,
    ) -> Path:
        resolved_path = path.expanduser().resolve()
        content = cls.serialize(cls.build(parameters, objects, armature))
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{resolved_path.name}.",
                suffix=".tmp",
                dir=resolved_path.parent,
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, resolved_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return resolved_path
