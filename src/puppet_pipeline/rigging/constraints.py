from __future__ import annotations

import math
from typing import Any

from puppet_pipeline.common import naming

IK_CHAINS = {
    "forearm.L": ("upper_arm.L", "hand_ctrl.L", "elbow_pole.L"),
    "forearm.R": ("upper_arm.R", "hand_ctrl.R", "elbow_pole.R"),
    "shin.L": ("thigh.L", "foot_ctrl.L", "knee_pole.L"),
    "shin.R": ("thigh.R", "foot_ctrl.R", "knee_pole.R"),
}


class ConstraintBuilder:
    def __init__(self, armature: Any) -> None:
        self.armature = armature

    def add_planar_ik(
        self,
        terminal_bone: Any,
        target_name: str,
        pole_name: str,
        chain_count: int = 2,
    ) -> Any:
        constraint = terminal_bone.constraints.new(type="IK")
        constraint.target = self.armature
        constraint.subtarget = target_name
        constraint.pole_target = self.armature
        constraint.pole_subtarget = pole_name
        constraint.pole_angle = (
            math.pi
            if terminal_bone.name in {"forearm.R", "shin.L"}
            else 0.0
        )
        constraint.chain_count = chain_count
        return constraint

    @staticmethod
    def _set_planar_ik_limits(pose_bone: Any) -> None:
        pose_bone.use_ik_limit_x = False
        pose_bone.use_ik_limit_y = False
        pose_bone.use_ik_limit_z = False

    @staticmethod
    def _add_fk_rotation_limit(pose_bone: Any) -> Any:
        constraint = pose_bone.constraints.new(type="LIMIT_ROTATION")
        constraint.owner_space = "LOCAL"
        constraint.use_limit_x = True
        constraint.min_x = 0.0
        constraint.max_x = 0.0
        constraint.use_limit_y = True
        constraint.min_y = 0.0
        constraint.max_y = 0.0
        constraint.use_limit_z = False
        return constraint

    def apply(self) -> None:
        pose_bones = self.armature.pose.bones
        for pose_bone in pose_bones:
            for constraint in list(pose_bone.constraints):
                if constraint.type in {"IK", "LIMIT_ROTATION"}:
                    pose_bone.constraints.remove(constraint)

        ik_bones = set()
        for terminal_name, (parent_name, target_name, pole_name) in IK_CHAINS.items():
            terminal_bone = pose_bones[terminal_name]
            self.add_planar_ik(terminal_bone, target_name, pole_name, chain_count=2)
            for bone_name in (terminal_name, parent_name):
                self._set_planar_ik_limits(pose_bones[bone_name])
                ik_bones.add(bone_name)

        for bone_name in naming.DEFORMING_BONE_NAMES:
            if bone_name not in ik_bones:
                self._add_fk_rotation_limit(pose_bones[bone_name])
