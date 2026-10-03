# Naming Contract v1

This contract defines names shared by character generation, skeletal rigging, verification, and
future animation-controller stages. Names are case-sensitive and MUST remain stable within naming
version 1.

## General Rules

- Names use ASCII lowercase `snake_case`.
- Bilateral items end in Blender-compatible `.L` or `.R`; the suffix is always last.
- Generated geometry objects use the `pup.` prefix. Bone names do not use a prefix.
- Blender's automatic numeric suffixes (`.001`, `.002`, etc.) are forbidden in completed output.
- A contract-breaking rename requires a `naming_version` increment and coordinated updates to all
  consuming stages.

## Collections and Armature

| Entity | Required name |
|--------|---------------|
| Root generated collection | `PUPPET` |
| Geometry collection | `PUPPET.GEOMETRY` |
| Rig collection | `PUPPET.RIG` |
| Armature object | `rig` |
| Armature datablock | `rig.data` |

## Geometry Objects

| Body part | Required object | Bound bone |
|-----------|-----------------|------------|
| Head | `pup.head` | `head` |
| Torso | `pup.torso` | `spine` |
| Left/right upper arm | `pup.upper_arm.L/R` | `upper_arm.L/R` |
| Left/right forearm | `pup.forearm.L/R` | `forearm.L/R` |
| Left/right hand | `pup.hand.L/R` | `hand.L/R` |
| Left/right thigh | `pup.thigh.L/R` | `thigh.L/R` |
| Left/right shin | `pup.shin.L/R` | `shin.L/R` |
| Left/right foot | `pup.foot.L/R` | `foot.L/R` |

Each mesh has exactly one deforming vertex group, and that group's name equals the bound bone name.

## Deforming Bones

Required central chain:

```text
hips
└── spine
    └── chest
        └── neck
            └── head
```

Required left/right limb chains:

```text
chest → shoulder.L/R → upper_arm.L/R → forearm.L/R → hand.L/R
hips  → thigh.L/R    → shin.L/R      → foot.L/R
```

`shoulder.L/R`, `chest`, and `neck` may have no geometry bound in v1 but remain deforming hierarchy
bones. Every other deforming bone listed above maps to the geometry table.

## Control Bones

| Purpose | Required names | Deforms |
|---------|----------------|---------|
| Hand IK targets | `hand_ctrl.L`, `hand_ctrl.R` | false |
| Foot IK targets | `foot_ctrl.L`, `foot_ctrl.R` | false |
| Elbow pole targets | `elbow_pole.L`, `elbow_pole.R` | false |
| Knee pole targets | `knee_pole.L`, `knee_pole.R` | false |

Control bones MUST NOT have vertex groups and MUST NOT appear as values in `objects[].bone`.

## Constraint Ownership

- Arm IK constraints belong to `forearm.L/R`; each targets `hand_ctrl.L/R`, uses
  `elbow_pole.L/R`, and has `chain_count = 2`.
- Leg IK constraints belong to `shin.L/R`; each targets `foot_ctrl.L/R`, uses `knee_pole.L/R`,
  and has `chain_count = 2`.
- Rotation-limit constraints use the Blender type identifier `LIMIT_ROTATION` and do not receive
  user-facing names as part of this contract.

## Reserved Names

Future animation controllers may add names under `anim_` (bones) and `PUPPET.ANIMATION`
(collection). Generation and skeletal-rigging stages MUST NOT create these reserved names.
