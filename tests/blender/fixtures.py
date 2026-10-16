from dataclasses import dataclass

from puppet_pipeline.common import naming
from puppet_pipeline.common.params import PuppetParameters
from puppet_pipeline.common.scene import PuppetCollections, reset_puppet_scene
from puppet_pipeline.generation.geometry import GeometryBuilder
from puppet_pipeline.generation.parts import PartSpec, build_part_specs
from puppet_pipeline.rigging.armature import ArmatureBuilder
from puppet_pipeline.rigging.binding import BindingApplier
from puppet_pipeline.rigging.constraints import ConstraintBuilder


@dataclass(frozen=True)
class RigFixture:
    collections: PuppetCollections
    parameters: PuppetParameters
    parts: tuple[PartSpec, ...]
    objects: dict
    armature: object


def build_rig_fixture(
    parameters: PuppetParameters | None = None,
) -> RigFixture:
    resolved_parameters = parameters or PuppetParameters()
    collections = reset_puppet_scene()
    parts = build_part_specs(resolved_parameters)
    objects = GeometryBuilder(collections.geometry).build(parts)
    specs = ArmatureBuilder.plan(resolved_parameters, parts)
    armature = ArmatureBuilder(collections.rig).build(specs)
    ConstraintBuilder(armature).apply()
    BindingApplier.bind(objects, armature)
    return RigFixture(
        collections=collections,
        parameters=resolved_parameters,
        parts=parts,
        objects=objects,
        armature=armature,
    )


def break_binding(
    fixture: RigFixture,
    object_name: str = "pup.forearm.L",
) -> str:
    if object_name not in naming.GEOMETRY_BINDINGS:
        raise ValueError(f"Unknown generated geometry object: {object_name}")
    obj = fixture.objects[object_name]
    bone_name = naming.GEOMETRY_BINDINGS[object_name]
    vertex_group = obj.vertex_groups.get(bone_name)
    if vertex_group is None:
        raise ValueError(f"Binding is already missing: {object_name} -> {bone_name}")
    obj.vertex_groups.remove(vertex_group)
    return bone_name


def break_ik_target(
    fixture: RigFixture,
    terminal_bone: str = "forearm.L",
) -> str:
    pose_bone = fixture.armature.pose.bones.get(terminal_bone)
    if pose_bone is None:
        raise ValueError(f"Unknown IK terminal bone: {terminal_bone}")
    constraints = [
        constraint
        for constraint in pose_bone.constraints
        if constraint.type == "IK"
    ]
    if len(constraints) != 1:
        raise ValueError(
            f"Expected one IK constraint on {terminal_bone}; found {len(constraints)}"
        )
    original_target = constraints[0].subtarget
    constraints[0].subtarget = "missing_ik_target"
    return original_target
