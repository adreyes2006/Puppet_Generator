# Data Model: 2D Stick-Figure Puppet Generation

## Entities

### PuppetParameters (input)

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| upper_arm_len | float | 1.0 | > 0 |
| forearm_len | float | 0.9 | > 0 |
| thigh_len | float | 1.2 | > 0 |
| shin_len | float | 1.1 | > 0 |
| limb_radius | float | 0.06 | > 0 |
| torso_len | float | 1.4 | > 0 |
| head_radius | float | 0.22 | > 0 |
| hip_width | float | 0.35 | > 0 |
| shoulder_width | float | 0.55 | > 0 |
| output_path | str | `puppet.blend` | writable parent dir |
| manifest_path | str | `<output>.manifest.json` | derived |
| seed | int | 0 | recorded, ≥ 0 |

Validation rule (FR-002): any non-positive numeric → fail fast, non-zero exit, no scene objects.

### PartSpec → Mesh Object (generation stage output)

| Field | Meaning |
|-------|---------|
| name | object name, e.g. `pup.forearm.L` (naming v1) |
| bone_name | deforming bone it binds to, e.g. `forearm.L` |
| origin, direction, length, radius | capsule placement in XZ plane |

Canonical part table (14 parts, symmetric): `head`, `torso`, `upper_arm.L/R`,
`forearm.L/R`, `hand.L/R`, `thigh.L/R`, `shin.L/R`, `foot.L/R`.

### BoneSpec → Edit/Pose Bone (rigging stage output)

| Field | Meaning |
|-------|---------|
| name | per naming v1 (`hips`, `spine`, `chest`, `neck`, `head`, `upper_arm.L`, …) |
| head, tail | joint positions derived from part origins/lengths |
| parent | parent bone name or `None` for `hips` |
| roll | set so local Z ∥ world +Y (planar hinge convention) |
| use_connect | true when child head coincides with parent tail |
| ik_chain | 2 for `upper_arm.*`/`thigh.*` (chain roots), 0 otherwise |
| deforms | false for `*_ctrl.*` and `*_pole.*` control bones |

Bone hierarchy (19 deforming + 8 control):

```text
hips (root)
├── spine → chest ──→ neck → head
│     ├── shoulder.L → upper_arm.L → forearm.L → hand.L
│     └── shoulder.R → upper_arm.R → forearm.R → hand.R
├── thigh.L → shin.L → foot.L
└── thigh.R → shin.R → foot.R
control (non-deforming, unparented or parented to hips):
hand_ctrl.L/R, foot_ctrl.L/R, elbow_pole.L/R, knee_pole.L/R
```

Constraints: `IK` on `forearm.L/R` (target `hand_ctrl.*`, pole `elbow_pole.*`) and
`shin.L/R` (target `foot_ctrl.*`, pole `knee_pole.*`), `chain_count=2`, with slight rest-pose
pre-bends and in-plane poles; `LIMIT_ROTATION` leaves local Z free on FK deforming bones.

### Binding Map

`part.bone_name → vertex group` — every vertex of the part's mesh assigned weight 1.0 to its
bone's group; one `ARMATURE` modifier per part object targeting the armature.

### Manifest (stage contract, schema v1)

```json
{
  "schema_version": 1,
  "naming_version": 1,
  "seed": 0,
  "parameters": { "…": "as PuppetParameters" },
  "objects": [{ "name": "pup.forearm.L", "bone": "forearm.L", "vertex_count": 24 }],
  "bones": [{ "name": "forearm.L", "parent": "upper_arm.L", "deforms": true, "ik_chain": 0 }],
  "control_bones": ["hand_ctrl.L", "…"],
  "constraints": [{ "bone": "upper_arm.L", "type": "IK", "target": "hand_ctrl.L",
                     "pole": "elbow_pole.L", "chain_count": 2 }]
}
```

## Validation Rules (from spec)

- Every mesh object in `objects[]` has a `bone` present in `bones[]` (contract test).
- Every vertex of every part is assigned to exactly one vertex group (FR-005, SC-002).
- `control_bones` all have `deforms=false` (stage boundary).
- Two runs with equal params+seed produce identical manifests (SC-005).

## State Transitions

`parameters → (validate) → PartSpecs → meshes → manifest.partial → BoneSpecs → armature →
constraints → bindings → manifest.complete → .blend saved`. Any stage failure aborts before
file save; re-run deletes prior `pup.*` objects / `rig` armature first (FR-011).
