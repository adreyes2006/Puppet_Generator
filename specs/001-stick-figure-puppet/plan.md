# Implementation Plan: 2D Stick-Figure Puppet Generation

**Branch**: `001-stick-figure-puppet` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-stick-figure-puppet/spec.md`

## Summary

A single entrypoint script (`generate_puppet.py`) runs inside Blender (`--background --python`),
parses limb-length/thickness parameters, and produces a `.blend` file containing a symmetric 2D
stick-figure puppet plus a JSON manifest. Internally the work is split into two constitution-mandated
stages: `generation/` builds the named flat mesh parts and emits the part manifest; `rigging/`
consumes that manifest, builds the armature (including planar-IK chains and FK controls), and binds
geometry via vertex groups. A `verify/` module provides the automated rig-movement checks from the
spec (P2). No keyframes, actions, or drivers are created — animation is a downstream stage.

## Technical Context

**Language/Version**: Python 3.13 (the interpreter bundled with the tested Blender 5.2.2 LTS); minimum supported Blender remains 4.2

**Primary Dependencies**: `bpy`, `bpy.types`, `bpy.data`, `bpy.ops` (minimal — mesh primitives only),
`mathutils` (`Vector`, `Matrix`), `json`, `argparse`, `dataclasses`, `enum` — all stdlib/Blender
bundled; no third-party packages required for generation.

**Storage**: Files only — output `.blend` + JSON manifest sidecar.

**Testing**: `pytest` for pure-Python units (parameters, manifest schema) and Blender-in-process
contract/smoke tests run via `blender --background --python tests/run_in_blender.py`.

**Target Platform**: Windows/Linux/macOS with Blender 4.2+; validated on Blender 5.2.2 LTS;
headless CI via `blender --background`.

**Project Type**: CLI tool / DCC automation script.

**Performance Goals**: Full generation < 60 s (target < 10 s); rig verification < 30 s.

**Constraints**: Strict stage separation per constitution; deterministic output (seeded);
stable documented naming; no animation data created.

**Scale/Scope**: One script package (~9 modules), 19 deforming bones, 8 control bones,
14 mesh parts, and one manifest schema.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Python-first, headless | PASS | Entrypoint is `generate_puppet.py`; all ops via `bpy`; runnable with `--background` |
| II. Stage separation | PASS | `generation/` emits manifest only; `rigging/` consumes manifest + meshes; no animation stage touched; `verify/` is read-only QA |
| III. Blender MCP rules | PASS | Design uses node-type lookups, RNA enum reads, no hardcoded localized names (see research.md) |
| IV. Deterministic artifacts | PASS | Seeded params recorded in manifest; fixed naming convention v1 |
| V. Test-first validation | PASS | Contract tests on manifest/bone names + smoke test rotating every bone |
| VI. Simplicity / YAGNI | PASS | Rigid vertex-group binding, built-in iTaSC-free legacy IK, no plugin system |

**Post-design re-check (2026-10-16)**: PASS. The data model, manifest/naming contracts, and
quickstart preserve the same stage boundaries and introduce no new dependency or animation-stage
work. No violations require Complexity Tracking.

## Architecture Overview

```text
generate_puppet.py            # CLI entrypoint: argparse → orchestrates stages → save .blend + manifest
src/puppet_pipeline/
├── common/
│   ├── params.py             # PuppetParameters dataclass + validation (FR-001/002)
│   ├── naming.py             # NAMING v1: bone/object/collection names, side suffixes
│   └── manifest.py           # ManifestWriter: schema v1 JSON emission
├── generation/
│   ├── geometry.py           # GeometryBuilder: creates part meshes in XZ plane
│   └── parts.py              # PartSpec dataclass + canonical part table (head, torso, limbs)
├── rigging/
│   ├── armature.py           # ArmatureBuilder + BoneSpec: edit-bone creation, hierarchy, rolls
│   ├── constraints.py        # ConstraintBuilder: planar IK chains + FK rotation limits
│   └── binding.py            # BindingApplier: vertex groups + armature modifier (rigid)
└── verify/
    ├── rig_check.py          # RigVerifier: pose each bone, measure vertex displacement
    └── run_in_blender.py     # Test harness for blender --background
tests/
├── unit/                     # pytest: params validation, naming, manifest schema
└── blender/                  # contract + smoke tests executed inside Blender
contracts/                    # (this dir) manifest.schema.json + naming.md
```

### Class Design (requested detail)

**`common/params.py`**
- `PuppetParameters` — frozen dataclass: `upper_arm_len`, `forearm_len`, `thigh_len`,
  `shin_len`, `limb_radius`, `torso_len`, `head_radius`, `hip_width`, `shoulder_width`, `seed`.
  `validate()` raises `ParameterError` on non-positive/non-numeric values (FR-002).

**`generation/geometry.py`**
- `PartSpec` — dataclass: `name`, `bone_name`, `length`, `radius`, `origin`, `direction`.
- `GeometryBuilder.build(parts: list[PartSpec]) -> dict[str, bpy.types.Object]` — creates one
  flat capsule/rounded-rect mesh per part in the **XZ plane** (thickness along +Y so the puppet
  reads as 2D from the −Y front view), names objects per naming v1, returns name→object map.

**`rigging/armature.py`**
- `BoneSpec` — dataclass: `name`, `head: Vector`, `tail: Vector`, `parent: str | None`,
  `roll: float`, `ik_chain: int` (0 = FK-only).
- `ArmatureBuilder`
  - `plan(params, parts) -> list[BoneSpec]` — derives joint positions from part geometry.
  - `build(specs) -> bpy.types.Object` — creates armature object + edit bones; sets `parent`,
    `use_connect` where joints touch; sets `roll` so every bone's **local Z axis points along
    world +Y** (out of the 2D plane) — this is what makes planar IK work (below).
  - Produces: `hips` (root) → `spine` → `chest` → `neck` → `head`; `shoulder.L/R` →
    `upper_arm.L/R` → `forearm.L/R` → `hand.L/R`; `thigh.L/R` → `shin.L/R` → `foot.L/R`;
    plus control bones `hand_ctrl.L/R`, `foot_ctrl.L/R` (IK targets, non-deforming) and
    `elbow_pole.L/R`, `knee_pole.L/R` (pole targets).

**`rigging/constraints.py`**
- `ConstraintBuilder`
  - `add_planar_ik(pose_bone, target, pole, chain_count)` — adds
    `bpy.types.KinematicConstraint` (`IK`) to the chain's terminal pose bone: `target=ctrl
    bone/object`, `pole_target`, `chain_count=2` (e.g., the constraint on `forearm` solves
    upper-arm + forearm toward `hand_ctrl`).
  - `add_rotation_limits(pose_bone)` — `bpy.types.LimitRotationConstraint` locking local X and Y
    (`use_limit_x/y=True`, `min=max=0`), leaving local Z (world Y hinge axis) free for FK. IK
    chains use slight rest-pose pre-bends and in-plane poles; movement tests enforce XZ confinement.

**`rigging/binding.py`**
- `BindingApplier.bind(objects, armature)` — per part: create vertex group named after its bone,
  assign all vertices weight 1.0 (rigid), add `ARMATURE` modifier; parents mesh to armature
  object. Pure binding only — does not alter geometry (stage boundary).

**`common/manifest.py`**
- `ManifestWriter.write(path, params, parts, armature)` — emits schema v1: params, seed,
  naming version, objects[], bones[] with parent links, control_bones[], vertex-group map.

**`verify/rig_check.py`**
- `RigVerifier` — for each deforming bone: record world-space head position of every bound
  vertex group, rotate bone ±15° about Y (via pose, `bpy.context.view_layer.update()`, read
  evaluated mesh via `obj.evaluated_get(depsgraph)`), assert bound verts displaced toward
  expected arc and unbound verts moved < ε; translate `hips` and assert all verts translate.

### bpy modules required

| Module | Use |
|--------|-----|
| `bpy.data` | create/retrieve meshes, objects, armatures, collections; cleanup on re-run |
| `bpy.ops.object` / `bpy.ops.mesh` | primitive creation (`primitive_cube_add`/`primitive_circle_add`) — kept minimal, prefer `bmesh`-free direct `mesh.from_pydata` for deterministic verts |
| `bpy.ops.object.mode_set` / `bpy.ops.object.editmode_toggle` | enter Edit mode for `Armature.edit_bones` |
| `bpy.types` | `Armature`, `EditBone`, `PoseBone`, `KinematicConstraint`, `LimitRotationConstraint`, `ArmatureModifier`, `VertexGroup` (type access + checks) |
| `bpy.context` | active object, `view_layer.update()`, depsgraph for evaluated meshes |
| `mathutils.Vector` / `Matrix` | joint math, bone rolls, world-space verification |
| `bpy.app` | version guard (`bpy.app.version >= (4,2,0)`) |

### Planar IK on the 2D plane (requested detail)

1. **Plane choice**: the puppet lives in the **XZ plane** (X = left/right, Z = up, Y = depth
   ≈ 0). All bone heads/tails have `y = 0`.
2. **Bone roll convention**: each edit bone's `roll` is set so the bone's local Z axis aligns
   with world +Y. Local Z is therefore the hinge axis for rotation within the XZ plane.
3. **Solver confinement**: FK bones use local-space rotation limits that lock X/Y and leave Z
   free. IK chains use symmetric rest-pose pre-bends plus pole targets that also lie in the XZ
   plane. Automated movement tests reject meaningful Y displacement.
4. **Chains**: `chain_count=2` per limb. The IK constraint is placed on the terminal chain
   bone (`forearm` driven by `hand_ctrl`, `shin` driven by `foot_ctrl`) and includes that bone
   plus its parent. In-plane `elbow_pole` and `knee_pole` controls select deterministic bend
   direction; mirrored chains use pole-angle compensation for consistent left/right behavior.
5. **Why built-in IK**: iTaSC was removed after Blender 2.79; modern Blender's built-in solver
   supports two-bone chains and pole targets natively.

## Project Structure

### Documentation (this feature)

```text
specs/001-stick-figure-puppet/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output: manifest.schema.json, naming.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
generate_puppet.py       # entrypoint: blender --background --python generate_puppet.py -- --params ...
src/puppet_pipeline/
├── common/{params.py, naming.py, manifest.py}
├── generation/{geometry.py, parts.py}
├── rigging/{armature.py, constraints.py, binding.py}
└── verify/{rig_check.py, run_in_blender.py}
tests/
├── unit/{test_params.py, test_naming.py, test_manifest.py}
└── blender/{test_contract.py, test_rig_movement.py}
```

**Structure Decision**: Single project. `generation/` and `rigging/` are separate packages
communicating only through the in-memory manifest + named objects (constitution II). `verify/`
is read-only over the produced `.blend` (constitution V).

## Complexity Tracking

No constitution violations — section intentionally empty.
