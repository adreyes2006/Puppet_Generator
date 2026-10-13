from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import bpy
from mathutils import Matrix, Vector

from puppet_pipeline.common import naming


class RigVerificationError(AssertionError):
    pass


@dataclass(frozen=True)
class MovementReport:
    subject: str
    moved_vertex_count: int
    moved_object_count: int = 0
    max_bound_displacement: float = 0.0
    max_unrelated_displacement: float = 0.0
    max_translation_error: float = 0.0
    control: str | None = None
    target_distance_error: float = 0.0
    max_y_displacement: float = 0.0
    pole_alignment: float = 0.0


class RigVerifier:
    def __init__(
        self,
        armature: Any,
        objects: Mapping[str, Any],
        epsilon: float = 1e-5,
    ) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be greater than zero")
        self.armature = armature
        self.objects = dict(objects)
        self.epsilon = epsilon

    def update_scene(self) -> None:
        bpy.context.view_layer.update()

    def capture_evaluated_vertices(self) -> dict[str, tuple[Vector, ...]]:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        captured = {}
        for name, obj in self.objects.items():
            evaluated_object = obj.evaluated_get(depsgraph)
            evaluated_mesh = evaluated_object.to_mesh()
            try:
                captured[name] = tuple(
                    evaluated_object.matrix_world @ vertex.co
                    for vertex in evaluated_mesh.vertices
                )
            finally:
                evaluated_object.to_mesh_clear()
        return captured

    def reset_pose(self) -> None:
        for pose_bone in self.armature.pose.bones:
            pose_bone.matrix_basis.identity()
        self.armature.update_tag()
        self.update_scene()

    def _pose_snapshot(self) -> dict[str, Matrix]:
        return {
            pose_bone.name: pose_bone.matrix_basis.copy()
            for pose_bone in self.armature.pose.bones
        }

    def _restore_pose(self, snapshot: Mapping[str, Matrix]) -> None:
        for bone_name, matrix in snapshot.items():
            self.armature.pose.bones[bone_name].matrix_basis = matrix
        self.armature.update_tag()
        self.update_scene()

    def _validate_bindings(self) -> None:
        for object_name, bone_name in naming.GEOMETRY_BINDINGS.items():
            obj = self.objects.get(object_name)
            if obj is None:
                raise RigVerificationError(f"missing geometry object {object_name}")
            group = obj.vertex_groups.get(bone_name)
            if group is None:
                raise RigVerificationError(
                    f"missing binding {object_name} -> {bone_name}"
                )
            for vertex in obj.data.vertices:
                assignments = [
                    assignment
                    for assignment in vertex.groups
                    if assignment.group == group.index
                ]
                if len(assignments) != 1 or not math.isclose(
                    assignments[0].weight,
                    1.0,
                    abs_tol=self.epsilon,
                ):
                    raise RigVerificationError(
                        f"invalid binding weight on {object_name} vertex {vertex.index}"
                    )

    @staticmethod
    def _displacements(
        before: tuple[Vector, ...],
        after: tuple[Vector, ...],
    ) -> tuple[float, ...]:
        if len(before) != len(after):
            raise RigVerificationError("evaluated vertex count changed during verification")
        return tuple((end - start).length for start, end in zip(before, after))

    def verify_bone_rotation(
        self,
        bone_name: str,
        angle_degrees: float = 15.0,
    ) -> MovementReport:
        self._validate_bindings()
        object_names = [
            object_name
            for object_name, bound_bone in naming.GEOMETRY_BINDINGS.items()
            if bound_bone == bone_name
        ]
        if len(object_names) != 1:
            raise RigVerificationError(
                f"{bone_name} must have exactly one bound geometry object"
            )
        object_name = object_names[0]
        snapshot = self._pose_snapshot()
        try:
            before = self.capture_evaluated_vertices()
            pose_bone = self.armature.pose.bones.get(bone_name)
            if pose_bone is None:
                raise RigVerificationError(f"missing pose bone {bone_name}")
            pose_bone.rotation_mode = "XYZ"
            pose_bone.rotation_euler.z += math.radians(angle_degrees)
            self.armature.update_tag()
            self.update_scene()
            after = self.capture_evaluated_vertices()

            bound_displacements = self._displacements(
                before[object_name],
                after[object_name],
            )
            unrelated_displacements = tuple(
                displacement
                for other_name in before
                if other_name != object_name
                for displacement in self._displacements(
                    before[other_name],
                    after[other_name],
                )
            )
            moved_vertex_count = sum(
                displacement > self.epsilon
                for displacement in bound_displacements
            )
            max_bound = max(bound_displacements, default=0.0)
            max_unrelated = max(unrelated_displacements, default=0.0)
            if moved_vertex_count == 0:
                raise RigVerificationError(
                    f"{bone_name} bound geometry did not move beyond epsilon"
                )
            if max_unrelated > self.epsilon:
                raise RigVerificationError(
                    f"{bone_name} moved unrelated geometry by {max_unrelated}"
                )
            return MovementReport(
                subject=bone_name,
                moved_vertex_count=moved_vertex_count,
                moved_object_count=1,
                max_bound_displacement=max_bound,
                max_unrelated_displacement=max_unrelated,
            )
        finally:
            self._restore_pose(snapshot)

    def verify_ik_control(
        self,
        terminal_name: str,
        control_name: str,
        pole_name: str,
        offset: Vector,
    ) -> MovementReport:
        self._validate_bindings()
        terminal = self.armature.pose.bones.get(terminal_name)
        control = self.armature.pose.bones.get(control_name)
        pole = self.armature.pose.bones.get(pole_name)
        if terminal is None or control is None or pole is None:
            raise RigVerificationError(
                f"missing IK element for {terminal_name}: {control_name}, {pole_name}"
            )
        constraints = [
            constraint
            for constraint in terminal.constraints
            if constraint.type == "IK"
        ]
        if len(constraints) != 1:
            raise RigVerificationError(
                f"{terminal_name} expected one IK constraint; found {len(constraints)}"
            )
        constraint = constraints[0]
        if constraint.target is not self.armature or constraint.subtarget != control_name:
            raise RigVerificationError(
                f"{terminal_name} has invalid IK target {constraint.subtarget!r}; "
                f"expected {control_name}"
            )
        if (
            constraint.pole_target is not self.armature
            or constraint.pole_subtarget != pole_name
        ):
            raise RigVerificationError(
                f"{terminal_name} has invalid pole target {constraint.pole_subtarget!r}; "
                f"expected {pole_name}"
            )

        snapshot = self._pose_snapshot()
        try:
            before = self.capture_evaluated_vertices()
            control.matrix = Matrix.Translation(Vector(offset)) @ control.matrix
            self.armature.update_tag()
            self.update_scene()
            after = self.capture_evaluated_vertices()

            target_error = (terminal.tail - control.head).length
            displacements = [
                end - start
                for object_name in before
                for start, end in zip(before[object_name], after[object_name])
            ]
            moved_vertex_count = sum(
                displacement.length > self.epsilon
                for displacement in displacements
            )
            max_y_displacement = max(
                (abs(displacement.y) for displacement in displacements),
                default=0.0,
            )

            chain_root = terminal.parent.head.copy()
            chain_end = terminal.tail.copy()
            chain_vector = chain_end - chain_root
            line_fraction = (terminal.head - chain_root).dot(chain_vector) / max(
                chain_vector.length_squared,
                self.epsilon,
            )
            line_point = chain_root + chain_vector * line_fraction
            bend_vector = terminal.head - line_point
            pole_vector = pole.head - line_point
            pole_alignment = bend_vector.dot(pole_vector)

            if moved_vertex_count == 0:
                raise RigVerificationError(
                    f"{terminal_name} IK control {control_name} moved no geometry"
                )
            if target_error > max(self.epsilon * 10, 5e-4):
                raise RigVerificationError(
                    f"{terminal_name} target distance error {target_error}"
                )
            if max_y_displacement > self.epsilon:
                raise RigVerificationError(
                    f"{terminal_name} left XZ plane by {max_y_displacement}"
                )
            if pole_alignment <= 0:
                raise RigVerificationError(
                    f"{terminal_name} bent away from pole {pole_name}"
                )

            return MovementReport(
                subject=terminal_name,
                control=control_name,
                moved_vertex_count=moved_vertex_count,
                target_distance_error=target_error,
                max_y_displacement=max_y_displacement,
                pole_alignment=pole_alignment,
            )
        finally:
            self._restore_pose(snapshot)

    def verify_root_translation(self, offset: Vector) -> MovementReport:
        self._validate_bindings()
        resolved_offset = Vector(offset)
        snapshot = self._pose_snapshot()
        try:
            before = self.capture_evaluated_vertices()
            root = self.armature.pose.bones.get("hips")
            if root is None:
                raise RigVerificationError("missing root bone hips")
            root.matrix = Matrix.Translation(resolved_offset) @ root.matrix
            self.armature.update_tag()
            self.update_scene()
            after = self.capture_evaluated_vertices()

            moved_vertex_count = 0
            moved_object_count = 0
            max_error = 0.0
            for object_name in before:
                object_moved = False
                for start, end in zip(before[object_name], after[object_name]):
                    displacement = end - start
                    if displacement.length > self.epsilon:
                        moved_vertex_count += 1
                        object_moved = True
                    max_error = max(
                        max_error,
                        (displacement - resolved_offset).length,
                    )
                moved_object_count += object_moved

            if moved_object_count != len(self.objects):
                raise RigVerificationError(
                    f"hips moved {moved_object_count} of {len(self.objects)} objects"
                )
            if max_error > self.epsilon:
                raise RigVerificationError(
                    f"hips translation error {max_error} exceeds epsilon"
                )
            return MovementReport(
                subject="hips",
                moved_vertex_count=moved_vertex_count,
                moved_object_count=moved_object_count,
                max_translation_error=max_error,
            )
        finally:
            self._restore_pose(snapshot)
