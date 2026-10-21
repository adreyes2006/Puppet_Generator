from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.generation.parts import PartSpec

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class BoneSpec:
    name: str
    head: Vector3
    tail: Vector3
    parent: str | None = None
    roll: float = 0.0
    use_connect: bool = False
    deforms: bool = True
    ik_chain: int = 0


class ArmatureBuilder:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    @staticmethod
    def plan(
        parameters: PuppetParameters,
        parts: tuple[PartSpec, ...] | list[PartSpec],
    ) -> tuple[BoneSpec, ...]:
        parameters.validate()
        parts_by_name = {part.name: part for part in parts}
        if set(parts_by_name) != set(naming.GEOMETRY_BINDINGS):
            raise ValueError("Armature planning requires the canonical 14-part table")

        torso_top = parameters.torso_len
        chest_base = torso_top * 0.65
        neck_length = parameters.head_radius * 0.25
        head_top = torso_top + parameters.head_radius * 2
        hip_left = (-parameters.hip_width / 2, 0.0, 0.0)
        hip_right = (parameters.hip_width / 2, 0.0, 0.0)
        center_hips = (0.0, 0.0, 0.0)
        center_chest = (0.0, 0.0, torso_top)
        specs = [
            BoneSpec("hips", hip_left, hip_right),
            BoneSpec("spine", center_hips, (0.0, 0.0, chest_base), "hips"),
            BoneSpec(
                "chest",
                (0.0, 0.0, chest_base),
                center_chest,
                "spine",
                use_connect=True,
            ),
            BoneSpec(
                "neck",
                center_chest,
                (0.0, 0.0, torso_top + neck_length),
                "chest",
                use_connect=True,
            ),
            BoneSpec(
                "head",
                (0.0, 0.0, torso_top + neck_length),
                (0.0, 0.0, head_top),
                "neck",
                use_connect=True,
            ),
        ]

        joints = {}
        for side, sign in (("L", -1.0), ("R", 1.0)):
            upper_arm = parts_by_name[f"pup.upper_arm.{side}"]
            forearm = parts_by_name[f"pup.forearm.{side}"]
            hand = parts_by_name[f"pup.hand.{side}"]
            thigh = parts_by_name[f"pup.thigh.{side}"]
            shin = parts_by_name[f"pup.shin.{side}"]
            foot = parts_by_name[f"pup.foot.{side}"]

            def endpoint(part: PartSpec) -> Vector3:
                return tuple(
                    part.origin[index] + part.direction[index] * part.length
                    for index in range(3)
                )

            shoulder = upper_arm.origin
            elbow = endpoint(upper_arm)
            wrist = endpoint(forearm)
            hand_tip = endpoint(hand)
            hip = thigh.origin
            knee = endpoint(thigh)
            ankle = endpoint(shin)
            toe = endpoint(foot)
            joints[side] = (elbow, wrist, knee, ankle)

            specs.extend(
                (
                    BoneSpec(
                        f"shoulder.{side}",
                        center_chest,
                        shoulder,
                        "chest",
                        use_connect=True,
                    ),
                    BoneSpec(
                        f"upper_arm.{side}",
                        shoulder,
                        elbow,
                        f"shoulder.{side}",
                        use_connect=True,
                    ),
                    BoneSpec(
                        f"forearm.{side}",
                        elbow,
                        wrist,
                        f"upper_arm.{side}",
                        use_connect=True,
                        ik_chain=2,
                    ),
                    BoneSpec(
                        f"hand.{side}",
                        wrist,
                        hand_tip,
                        f"forearm.{side}",
                        use_connect=True,
                    ),
                    BoneSpec(f"thigh.{side}", hip, knee, "hips"),
                    BoneSpec(
                        f"shin.{side}",
                        knee,
                        ankle,
                        f"thigh.{side}",
                        use_connect=True,
                        ik_chain=2,
                    ),
                    BoneSpec(
                        f"foot.{side}",
                        ankle,
                        toe,
                        f"shin.{side}",
                        use_connect=True,
                    ),
                )
            )

        control_length = parameters.limb_radius * 2
        pole_y = max(
            parameters.upper_arm_len,
            parameters.forearm_len,
            parameters.thigh_len,
            parameters.shin_len,
        ) * 0.5
        for side, sign in (("L", -1.0), ("R", 1.0)):
            elbow, wrist, knee, ankle = joints[side]
            specs.extend(
                (
                    BoneSpec(
                        f"hand_ctrl.{side}",
                        wrist,
                        (wrist[0], 0.0, wrist[2] + control_length),
                        "hips",
                        deforms=False,
                    ),
                    BoneSpec(
                        f"foot_ctrl.{side}",
                        ankle,
                        (ankle[0], 0.0, ankle[2] + control_length),
                        "hips",
                        deforms=False,
                    ),
                    BoneSpec(
                        f"elbow_pole.{side}",
                        (elbow[0], 0.0, elbow[2] - pole_y),
                        (elbow[0], 0.0, elbow[2] - pole_y + control_length),
                        "hips",
                        deforms=False,
                    ),
                    BoneSpec(
                        f"knee_pole.{side}",
                        (knee[0] + sign * pole_y, 0.0, knee[2]),
                        (knee[0] + sign * pole_y, 0.0, knee[2] + control_length),
                        "hips",
                        deforms=False,
                    ),
                )
            )

        specs_by_name = {spec.name: spec for spec in specs}
        ordered_names = naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES
        if set(specs_by_name) != set(ordered_names):
            raise ValueError("Armature plan does not match naming contract v1")
        return tuple(specs_by_name[name] for name in ordered_names)

    def build(self, specs: tuple[BoneSpec, ...] | list[BoneSpec]) -> Any:
        import bpy
        from mathutils import Vector

        specs_by_name = {spec.name: spec for spec in specs}
        expected_names = set(naming.DEFORMING_BONE_NAMES + naming.CONTROL_BONE_NAMES)
        if set(specs_by_name) != expected_names or len(specs_by_name) != len(specs):
            raise ValueError("Armature build requires one BoneSpec per naming-v1 bone")
        for spec in specs:
            if spec.parent is not None and spec.parent not in specs_by_name:
                raise ValueError(f"Unknown parent {spec.parent!r} for bone {spec.name!r}")

        active_object = bpy.context.view_layer.objects.active
        if active_object is not None and active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        view_layer = bpy.context.view_layer
        for obj in getattr(view_layer.objects, "selected", []):
            obj.select_set(False)

        existing = bpy.data.objects.get(naming.ARMATURE_OBJECT_NAME)
        if existing is not None:
            existing_data = existing.data
            bpy.data.objects.remove(existing, do_unlink=True)
            if (
                existing_data is not None
                and existing_data.users == 0
                and existing_data.name in bpy.data.armatures
            ):
                bpy.data.armatures.remove(existing_data)
        existing_data = bpy.data.armatures.get(naming.ARMATURE_DATA_NAME)
        if existing_data is not None and existing_data.users == 0:
            bpy.data.armatures.remove(existing_data)

        armature_data = bpy.data.armatures.new(naming.ARMATURE_DATA_NAME)
        armature_object = bpy.data.objects.new(
            naming.ARMATURE_OBJECT_NAME,
            armature_data,
        )
        self.collection.objects.link(armature_object)
        armature_object.show_in_front = True
        armature_object.select_set(True)
        bpy.context.view_layer.objects.active = armature_object

        mode_override = dict(
            object=armature_object,
            active_object=armature_object,
            selected_objects=[armature_object],
            selected_editable_objects=[armature_object],
        )
        with bpy.context.temp_override(**mode_override):
            bpy.ops.object.mode_set(mode="EDIT")
        try:
            for spec in specs:
                edit_bone = armature_data.edit_bones.new(spec.name)
                edit_bone.head = Vector(spec.head)
                edit_bone.tail = Vector(spec.tail)
                edit_bone.roll = spec.roll
                edit_bone.use_deform = spec.deforms

            for spec in specs:
                edit_bone = armature_data.edit_bones[spec.name]
                if spec.parent is not None:
                    edit_bone.parent = armature_data.edit_bones[spec.parent]
                    edit_bone.use_connect = spec.use_connect
                edit_bone.align_roll(Vector((0.0, 1.0, 0.0)))
        finally:
            with bpy.context.temp_override(**mode_override):
                bpy.ops.object.mode_set(mode="OBJECT")

        return armature_object
