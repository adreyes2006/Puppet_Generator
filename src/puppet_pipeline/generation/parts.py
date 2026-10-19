import math
from dataclasses import dataclass

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class PartSpec:
    name: str
    bone_name: str
    length: float
    radius: float
    origin: Vector3
    direction: Vector3


def _part(
    name: str,
    length: float,
    radius: float,
    origin: Vector3,
    direction: Vector3,
) -> PartSpec:
    return PartSpec(
        name=name,
        bone_name=naming.GEOMETRY_BINDINGS[name],
        length=length,
        radius=radius,
        origin=origin,
        direction=direction,
    )


def build_part_specs(parameters: PuppetParameters) -> tuple[PartSpec, ...]:
    parameters.validate()

    shoulder_z = parameters.torso_len
    shoulder_x = parameters.shoulder_width / 2
    hip_x = parameters.hip_width / 2
    hand_length = parameters.limb_radius * 3
    foot_length = parameters.limb_radius * 4
    arm_bend = min(
        parameters.limb_radius,
        parameters.upper_arm_len * 0.1,
        parameters.forearm_len * 0.1,
    )
    leg_bend = min(
        parameters.limb_radius,
        parameters.thigh_len * 0.1,
        parameters.shin_len * 0.1,
    )
    upper_arm_x = math.sqrt(parameters.upper_arm_len**2 - arm_bend**2)
    forearm_x = math.sqrt(parameters.forearm_len**2 - arm_bend**2)
    thigh_z = math.sqrt(parameters.thigh_len**2 - leg_bend**2)
    shin_z = math.sqrt(parameters.shin_len**2 - leg_bend**2)

    parts = [
        _part(
            "pup.head",
            parameters.head_radius * 2,
            parameters.head_radius,
            (0.0, 0.0, shoulder_z),
            (0.0, 0.0, 1.0),
        ),
        _part(
            "pup.torso",
            parameters.torso_len,
            parameters.shoulder_width / 2,
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
    ]

    for side, sign in (("L", -1.0), ("R", 1.0)):
        upper_arm_origin = (sign * shoulder_x, 0.0, shoulder_z)
        forearm_origin = (
            sign * (shoulder_x + upper_arm_x),
            0.0,
            shoulder_z - arm_bend,
        )
        hand_origin = (
            sign * (shoulder_x + upper_arm_x + forearm_x),
            0.0,
            shoulder_z,
        )
        leg_origin = (sign * hip_x, 0.0, 0.0)
        shin_origin = (
            sign * (hip_x + leg_bend),
            0.0,
            -thigh_z,
        )
        foot_origin = (
            sign * hip_x,
            0.0,
            -(thigh_z + shin_z),
        )
        outward = (sign, 0.0, 0.0)

        parts.extend(
            (
                _part(
                    f"pup.upper_arm.{side}",
                    parameters.upper_arm_len,
                    parameters.limb_radius,
                    upper_arm_origin,
                    (
                        sign * upper_arm_x / parameters.upper_arm_len,
                        0.0,
                        -arm_bend / parameters.upper_arm_len,
                    ),
                ),
                _part(
                    f"pup.forearm.{side}",
                    parameters.forearm_len,
                    parameters.limb_radius,
                    forearm_origin,
                    (
                        sign * forearm_x / parameters.forearm_len,
                        0.0,
                        arm_bend / parameters.forearm_len,
                    ),
                ),
                _part(
                    f"pup.hand.{side}",
                    hand_length,
                    parameters.limb_radius,
                    hand_origin,
                    outward,
                ),
                _part(
                    f"pup.thigh.{side}",
                    parameters.thigh_len,
                    parameters.limb_radius,
                    leg_origin,
                    (
                        sign * leg_bend / parameters.thigh_len,
                        0.0,
                        -thigh_z / parameters.thigh_len,
                    ),
                ),
                _part(
                    f"pup.shin.{side}",
                    parameters.shin_len,
                    parameters.limb_radius,
                    shin_origin,
                    (
                        -sign * leg_bend / parameters.shin_len,
                        0.0,
                        -shin_z / parameters.shin_len,
                    ),
                ),
                _part(
                    f"pup.foot.{side}",
                    foot_length,
                    parameters.limb_radius,
                    foot_origin,
                    outward,
                ),
            )
        )

    parts_by_name = {part.name: part for part in parts}
    return tuple(parts_by_name[name] for name in naming.GEOMETRY_BINDINGS)
