---

description: "Dependency-ordered implementation checklist for the 2D stick-figure puppet"
---

# Tasks: 2D Stick-Figure Puppet Generation

**Input**: Design documents from `/specs/001-stick-figure-puppet/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the feature specification and constitution. For each behavior, write the
listed test first, confirm it fails, then implement the corresponding production task.

**Organization**: Tasks are grouped by user story and ordered so script/package foundations precede
geometry, geometry precedes armature construction, and armature construction precedes binding.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks at that point because it touches different files
  and has no dependency on their incomplete work.
- **[Story]**: Maps the task to a user story in `spec.md`.
- Every task includes an exact repository-relative file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the Python/Blender package and test layout before any scene logic.

- [X] T001 Create the package/test directory structure and empty package initializers in `src/puppet_pipeline/__init__.py`, `src/puppet_pipeline/common/__init__.py`, `src/puppet_pipeline/generation/__init__.py`, `src/puppet_pipeline/rigging/__init__.py`, `src/puppet_pipeline/verify/__init__.py`, `tests/unit/__init__.py`, and `tests/blender/__init__.py`
- [X] T002 Create the minimal Blender entrypoint in `generate_puppet.py` with `bpy` and `bpy.app` imports, `--` argument separation, Blender 4.2+ version guard, and a `main()` function that returns a process status without creating scene data
- [X] T003 [P] Create the Blender background test launcher in `tests/blender/run_in_blender.py` that discovers Blender test modules, reports assertion failures, and exits non-zero
- [X] T004 [P] Add shared pytest path/bootstrap configuration for importing `src/puppet_pipeline` in `tests/conftest.py`

**Checkpoint**: `blender --background --factory-startup --python generate_puppet.py -- --help`
loads the entrypoint without import or version errors, and the empty test launchers execute.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared parameter, naming, cleanup, and manifest primitives required by every
user story. No geometry or rigging task may start before this phase is complete.

**CRITICAL**: Complete tasks in numerical order unless marked `[P]` at the same dependency level.

- [X] T005 [P] Write failing tests for all naming-v1 constants, `.L`/`.R` suffix rules, reserved `anim_` names, and rejection of Blender numeric suffixes in `tests/unit/test_naming.py`
- [X] T006 [P] Write failing tests for `PuppetParameters` defaults and validation in `tests/unit/test_params.py`, covering the verbatim constraints “all dimensions > 0,” “seed ≥ 0,” and rejection of non-numeric input
- [X] T007 Implement naming-v1 object, bone, collection, control, and reserved-name constants from `contracts/naming.md` in `src/puppet_pipeline/common/naming.py` to pass T005
- [X] T008 Implement frozen `PuppetParameters` plus `ParameterError` and validation in `src/puppet_pipeline/common/params.py` to pass T006, using defaults from `data-model.md` and validating before any `bpy.data` mutation
- [X] T009 Write failing Blender tests for generated-collection cleanup and idempotent same-session setup in `tests/blender/test_scene_setup.py`
- [X] T010 Implement deterministic collection creation and cleanup of prior `PUPPET`, `PUPPET.GEOMETRY`, `PUPPET.RIG`, `pup.*`, and `rig` data in `src/puppet_pipeline/common/scene.py` to pass T009 without touching unrelated scene objects
- [X] T011 Implement CLI parsing for every `PuppetParameters` field plus `--output` and `--manifest` in `generate_puppet.py`, ensuring parameter validation and writable-parent checks complete before T010 scene setup runs

**Checkpoint**: Pure unit tests pass; invalid input exits non-zero without creating scene objects or
output files; repeated scene setup leaves one empty puppet hierarchy.

---

## Phase 3: User Story 1 — Generate a Parameterized Stick-Figure Puppet (Priority: P1) MVP

**Goal**: One headless command creates a parameterized 2D puppet, skeletal armature, planar IK
controls, rigid bindings, and a saved `.blend` file.

**Independent Test**: Run generation with defaults and custom proportions; inspect the resulting
`.blend` and confirm all 14 geometry objects, 19 deforming bones, 8 control bones, four planar IK
chains, complete rigid binding, and no animation data.

### Tests for User Story 1

- [X] T012 [P] [US1] Write failing pure unit tests for the canonical 14 `PartSpec` records, bilateral symmetry, parameter-to-length/radius mapping, and XZ-plane placement in `tests/unit/test_parts.py`
- [X] T013 [P] [US1] Write failing Blender geometry contract tests for object names, flat XZ placement, positive vertex counts, parameterized dimensions, and `PUPPET.GEOMETRY` membership in `tests/blender/test_geometry.py`
- [X] T014 [P] [US1] Write failing Blender armature contract tests for the exact 19-deforming/8-control bone hierarchy, `use_deform` flags, connected joints, and local-Z/world-+Y roll convention in `tests/blender/test_armature.py`
- [X] T015 [P] [US1] Write failing Blender IK tests asserting constraints live on `forearm.L/R` and `shin.L/R`, target the matching controls and poles, use `chain_count=2`, slight rest pre-bends, and in-plane pole controls in `tests/blender/test_ik.py`
- [X] T016 [P] [US1] Write failing Blender binding tests asserting every mesh vertex belongs to exactly one matching deform-bone group at weight `1.0` and every mesh has one armature modifier targeting `rig` in `tests/blender/test_binding.py`
- [X] T017 [P] [US1] Write the failing headless smoke test for default/custom generation, `.blend` save, safe same-session re-run, and absence of actions, keyframes, drivers, and `PUPPET.ANIMATION` in `tests/blender/test_generation_smoke.py`

### Character Generation for User Story 1

- [X] T018 [US1] Implement `PartSpec` and the canonical parameter-derived part table for head, torso, bilateral arms/hands, and bilateral legs/feet in `src/puppet_pipeline/generation/parts.py` to pass T012
- [X] T019 [US1] Implement deterministic capsule/rounded-part mesh construction with `mesh.from_pydata`, XZ-plane coordinates, +Y thickness, naming-v1 objects, and `PUPPET.GEOMETRY` linking in `src/puppet_pipeline/generation/geometry.py` to pass T013; do not create armatures, constraints, or animation data

### Skeletal Rigging for User Story 1

- [X] T020 [US1] Implement `BoneSpec` and `ArmatureBuilder.plan()` joint-position derivation from generated part records in `src/puppet_pipeline/rigging/armature.py`, with no geometry mutation
- [X] T021 [US1] Complete `ArmatureBuilder.build()` in `src/puppet_pipeline/rigging/armature.py` to create the naming-v1 `rig` armature, exact hierarchy, deform/control flags, connected bones, and planar roll convention required by T014
- [X] T022 [US1] Implement `ConstraintBuilder.add_planar_ik()` and FK rotation limits in `src/puppet_pipeline/rigging/constraints.py` to pass T015, placing two-bone IK on terminal bones with deterministic in-plane poles and no drivers, actions, or keyframes
- [X] T023 [US1] Implement `BindingApplier.bind()` in `src/puppet_pipeline/rigging/binding.py` to pass T016, assigning each part's vertices to exactly one naming-matched group at weight `1.0`, adding one armature modifier, and not altering generated mesh topology

### Integration for User Story 1

- [X] T024 [US1] Wire validation → cleanup → character generation → armature generation → constraints → binding → `.blend` save in dependency order in `generate_puppet.py`, aborting without partial output on failure
- [X] T025 [US1] Make the headless generation smoke test pass in `tests/blender/test_generation_smoke.py` for default values, ≥20% custom dimension changes, repeat runs, and animation-stage exclusions

**Checkpoint**: User Story 1 is a complete MVP; execute Quickstart sections 2, 3, and the structural
portion of section 4 without a manifest requirement.

---

## Phase 4: User Story 2 — Automated Rig Movement Verification (Priority: P2)

**Goal**: Automatically pose every deforming limb and root, validate expected bound-geometry
movement, and prove the four IK chains remain in the 2D plane.

**Independent Test**: Run verification against one valid generated puppet (passes) and one fixture
with a removed vertex-group assignment or wrong IK target (fails with the affected bone/object).

### Tests for User Story 2

- [X] T026 [P] [US2] Write failing movement-verifier tests for ±15° FK rotation, root translation, evaluated bound/unbound vertex displacement, epsilon handling, and pose reset in `tests/blender/test_rig_movement.py`
- [X] T027 [P] [US2] Write failing planar-IK verifier tests for hand/foot target movement, intended elbow/knee pole bend direction, and negligible Y displacement in `tests/blender/test_planar_ik_movement.py`
- [X] T028 [P] [US2] Add deliberately broken binding and IK-target fixtures that must produce precise verification failures in `tests/blender/fixtures.py`

### Implementation for User Story 2

- [X] T029 [US2] Implement evaluated-depsgraph vertex sampling, bone-local ±15° pose application, root translation comparison, epsilon checks, and guaranteed pose restoration in `src/puppet_pipeline/verify/rig_check.py` to pass T026
- [X] T030 [US2] Extend `RigVerifier` with hand/foot control movement and XZ-plane/pole-direction assertions in `src/puppet_pipeline/verify/rig_check.py` to pass T027 and T028
- [X] T031 [US2] Connect `tests/blender/run_in_blender.py` to load `--blend` and run the contract/movement suites against generated and broken fixtures, returning non-zero with bone/object diagnostics on failure

**Checkpoint**: The valid puppet passes all movement checks; broken binding and IK fixtures fail for
the expected reason; pose state is unchanged after verification.

---

## Phase 5: User Story 3 — Manifest & Naming Contract for Downstream Stages (Priority: P3)

**Goal**: Emit a deterministic schema-v1 JSON sidecar that exactly describes parameters, geometry,
bones, controls, constraints, and binding relationships for downstream animation controllers.

**Independent Test**: Generate a puppet, validate the sidecar against the schema, compare every
listed entity to the `.blend`, and byte-compare manifests from two equal-input runs.

### Tests for User Story 3

- [X] T032 [P] [US3] Write failing unit tests for deterministic field ordering/content and schema-v1 serialization of parameters, 14 objects, 19 deforming bones, 8 controls, and constraints in `tests/unit/test_manifest.py`
- [X] T033 [P] [US3] Write failing Blender contract tests that compare manifest objects, bones, hierarchy, deform flags, control bones, constraints, vertex counts, and binding names to the live `.blend` in `tests/blender/test_manifest_contract.py`
- [X] T034 [P] [US3] Write a failing determinism test that byte-compares manifests from two runs with identical parameters/seed and checks changed dimensions/seed are recorded in `tests/blender/test_manifest_determinism.py`

### Implementation for User Story 3

- [X] T035 [US3] Implement `ManifestWriter` schema-v1 deterministic serialization and atomic file replacement in `src/puppet_pipeline/common/manifest.py` to pass T032, conforming to `specs/001-stick-figure-puppet/contracts/manifest.schema.json`
- [X] T036 [US3] Integrate manifest emission after successful binding and before final `.blend` publication in `generate_puppet.py`, removing temporary/partial outputs on failure and passing T033
- [X] T037 [US3] Stabilize manifest ordering and seed/parameter recording in `src/puppet_pipeline/common/manifest.py` until T034 passes byte-for-byte

**Checkpoint**: User Story 3 provides a stable, independently readable downstream contract; all
manifest, naming, and determinism tests pass.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the integrated pipeline and MCP workflow without introducing new scope.

- [X] T038 [P] Add concise command usage and parameter help text matching the defaults and validation rules in `generate_puppet.py`
- [X] T039 Run all pure-Python tests and fix regressions without weakening assertions: `python -m pytest tests/unit`
- [X] T040 Run the complete background Blender suite and fix regressions without changing contracts: `blender --background --factory-startup --python tests/blender/run_in_blender.py`
- [X] T041 Execute every scenario in `specs/001-stick-figure-puppet/quickstart.md`, including invalid-input, custom-proportion, movement, determinism, and same-session rerun checks
- [X] T042 Use Blender MCP to call `get_addon_status()` and `get_scene_info()`, load the generated default puppet, inspect a posed IK control, then confirm with `get_viewport_screenshot()` and `get_scene_info()`; record only discovered test failures in the applicable `tests/blender/*.py` file
- [X] T043 Perform a final stage-boundary audit of `src/puppet_pipeline/generation/`, `src/puppet_pipeline/rigging/`, and `src/puppet_pipeline/verify/` against `.specify/memory/constitution.md`, ensuring generation creates no rig data, rigging changes no geometry topology, and neither creates animation-controller data

---

## Dependencies & Execution Order

### Strict Phase Dependencies

```text
Phase 1 Setup
  → Phase 2 Foundation
    → Phase 3 US1: parts → geometry → armature → IK constraints → binding → integration
      → Phase 4 US2: verification
      → Phase 5 US3: manifest contract
        → Phase 6 integrated validation
```

- **Phase 1** has no dependencies.
- **Phase 2** depends on Phase 1 and blocks every user story.
- **US1** depends on Phase 2. Within US1, T018 → T019 → T020 → T021 → T022 → T023 → T024
  is strict; this enforces geometry before armature and armature before binding.
- **US2** depends on a valid US1-generated `.blend`; its test authoring tasks T026–T028 can run in
  parallel, then implementation follows T029 → T030 → T031.
- **US3** depends on US1 scene objects/bindings but not on US2; after US1, US2 and US3 may be
  implemented in parallel by different developers. T032–T034 can run in parallel, followed by
  T035 → T036 → T037.
- **Phase 6** depends on all selected stories; T039–T043 are sequential because later checks rely
  on earlier automated tests being green.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundation; no story dependency; suggested MVP.
- **US2 (P2)**: Requires US1's generated rig as its verification subject.
- **US3 (P3)**: Requires US1's generated objects, bones, constraints, and bindings to serialize.
- **US2 and US3**: Independent of each other once US1 is complete.

### Parallel Opportunities

- T003 and T004 can proceed in parallel after T002 establishes the entrypoint contract.
- T005 and T006 are parallel test-authoring tasks; T007 and T008 then implement separate modules.
- T012–T017 can be authored in parallel before US1 implementation begins.
- T026–T028 can be authored in parallel after the US1 fixture shape is stable.
- T032–T034 can be authored in parallel after the US1 object model is stable.
- US2 and US3 can be implemented in parallel after US1 passes its checkpoint.

## Parallel Examples

### User Story 1

```text
Task T012: PartSpec/parameter mapping tests in tests/unit/test_parts.py
Task T013: Geometry contract tests in tests/blender/test_geometry.py
Task T014: Armature hierarchy tests in tests/blender/test_armature.py
Task T015: Planar IK structure tests in tests/blender/test_ik.py
Task T016: Binding contract tests in tests/blender/test_binding.py
Task T017: End-to-end generation smoke test in tests/blender/test_generation_smoke.py
```

### User Story 2

```text
Task T026: FK/root movement tests in tests/blender/test_rig_movement.py
Task T027: IK-plane movement tests in tests/blender/test_planar_ik_movement.py
Task T028: Broken-rig fixtures in tests/blender/fixtures.py
```

### User Story 3

```text
Task T032: Manifest serialization tests in tests/unit/test_manifest.py
Task T033: Live-scene manifest contract tests in tests/blender/test_manifest_contract.py
Task T034: Manifest determinism tests in tests/blender/test_manifest_determinism.py
```

## Implementation Strategy

### MVP First

1. Complete Setup (T001–T004).
2. Complete Foundation (T005–T011).
3. Complete US1 tests first (T012–T017) and observe failures.
4. Implement US1 strictly in order (T018–T025).
5. Stop and validate the generated, rigged puppet before adding verifier or manifest functionality.

### Incremental Delivery

1. **MVP**: US1 — command generates and saves a parameterized, bound, planar-IK puppet.
2. **Quality increment**: US2 — automatic movement/IK verification catches broken rigs.
3. **Integration increment**: US3 — deterministic manifest enables downstream controllers.
4. **Release gate**: Phase 6 — all headless and MCP-assisted checks pass.

## Notes

- `[P]` never overrides phase or explicitly stated task dependencies.
- Tests must fail for the intended missing behavior before production implementation begins.
- Do not add keyframes, actions, drivers, or animation controllers in any task.
- Do not move geometry creation into `rigging/` or armature creation into `generation/`.
- Do not weaken tests to accommodate implementation defects; fix the production behavior.
