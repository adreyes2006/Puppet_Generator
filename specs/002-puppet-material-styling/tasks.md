# Tasks: Puppet Material and Accessory Styling

**Input**: Design documents from `/specs/002-puppet-material-styling/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story (P1→P5) to enable independent implementation and
testing. Tests are written FIRST and must FAIL before implementation (constitution Principle V).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps to spec user story (US1–US5)
- File paths are repository-root relative

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Styling package skeleton, entrypoint, and failing contract tests scaffolding

- [X] T001 Create `src/puppet_pipeline/styling/__init__.py` (empty) and `style_puppet.py` entrypoint stub importing `bpy`, `bpy.app`, Blender version guard `>= (4,2,0)`, `--` argument separation, and side-effect-free `main()` — mirrors `generate_puppet.py` conventions
- [X] T002 [P] Write failing naming-v1.1 tests in `tests/unit/test_styling_naming.py`: `acc.*`, `bg.*`, `bg.prop.*`, `mat.*` prefixes, `PUPPET.STYLE`/`PUPPET.STYLE.ACCESSORIES`/`PUPPET.STYLE.BACKGROUND` collection names, terminal `.L`/`.R` on bilateral accessories, no `.001` suffixes, no `anim_`/`PUPPET.ANIMATION` names
- [X] T003 [P] Write failing material-catalog tests in `tests/unit/test_material_catalog.py`: ≥10 presets, unique names, `base_color`/`roughness`/`metallic`/`emission_*`/`fill_mode` fields, all channels finite in 0.0–1.0
- [X] T004 [P] Write failing preset-schema tests in `tests/unit/test_styling_presets.py`: strict `styling-preset-v1` parse, `fill_mode ∈ {solid, outline}`, part-name keys without `pup.` prefix, accessory `attach_bone ∈ {foot.L, foot.R, head}`, reject unknown keys, portable filename validation `[A-Za-z0-9._-]+`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure data models, naming constants, manifest writer, and scene validation shared by all stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement styling naming constants in `src/puppet_pipeline/styling/naming.py` per `contracts/styling-naming.md` (v1.1) — must make T002 pass
- [X] T006 [P] Implement `MaterialPreset` frozen dataclass + `MATERIAL_CATALOG` (≥10 presets: matte colors, skin tones, metallic, glowing) in `src/puppet_pipeline/styling/materials.py` — must make T003 pass
- [X] T007 Implement `StylingPreset` load/save/validate against `contracts/preset.schema.json` in `src/puppet_pipeline/styling/presets.py` (pure-Python parts only; `apply`/`reset` deferred to US5) — must make T004 pass
- [X] T008 Implement `StylingManifestWriter.write(path, state)` emitting deterministic `styling-v1` JSON per `contracts/styling.schema.json` in `src/puppet_pipeline/styling/manifest.py` (fields: `schema`, `source_manifest`, `blender_version`, `fill_mode`, `materials`, `accessories`, `background`, `preview_files`)
- [X] T009 Implement `setup_style_collections()` and `validate_puppet_scene()` in `src/puppet_pipeline/styling/scene.py`: require `rig` + all 14 `pup.*` objects or raise before mutating; warn (non-fatal) when part structure differs from the canonical spec (modified-geometry edge case); create `PUPPET.STYLE` → `PUPPET.STYLE.ACCESSORIES`/`PUPPET.STYLE.BACKGROUND` collection tree

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Apply Body Materials (Priority: P1) 🎯 MVP

**Goal**: Assign material presets to any of the 14 body parts and toggle solid/outline fill mode

**Independent Test**: Load generated puppet, apply `torso=blue`, verify `mat.blue` on `pup.torso`
with Principled BSDF inputs set; toggle outline mode and verify Wireframe modifiers on all `pup.*`
only

### Tests for User Story 1 ⚠️ Write FIRST, ensure FAIL

- [X] T010 [P] [US1] Blender contract tests in `tests/blender/test_materials.py`: apply preset → object has exactly one `mat.*` material; Principled node found by `type=='BSDF_PRINCIPLED'`; base_color/roughness/metallic match preset; re-application reuses same datablock (no `.001`)
- [X] T011 [P] [US1] Blender fill-mode tests in `tests/blender/test_fill_mode.py`: outline mode adds `WIREFRAME` modifier to all 14 `pup.*` and only those; modifier ordered AFTER Armature modifier; solid mode removes them; `acc.*`/`bg.*` never get modifiers

### Implementation for User Story 1

- [X] T012 [US1] Implement `MaterialApplier` in `src/puppet_pipeline/styling/materials.py`: `apply(object_name, preset_name)` creates/reuses `mat.<preset>` datablock with `use_nodes`, sets Principled BSDF inputs by node `type` lookup (constitution III), assigns to object material slot; deterministic datablock reuse
- [X] T013 [US1] Implement `set_fill_mode('solid'|'outline')` in `src/puppet_pipeline/styling/materials.py`: add/remove `WIREFRAME` modifier (`use_replace=True`, thickness ∝ `limb_thickness`) on all `pup.*` objects only, preserving Armature modifier order
- [X] T014 [US1] Wire `--material <part>=<preset>` (repeatable) and `--fill-mode` CLI flags in `style_puppet.py`; validate preset/part names before scene mutation

**Checkpoint**: US1 fully functional — any part can be colored and fill mode toggled independently

---

## Phase 4: User Story 2 — Add Accessories (Priority: P2)

**Goal**: Attach procedural shoes/hats to foot/head bones; they follow limb movement

**Independent Test**: Apply sneakers to both feet; `acc.shoe.sneakers.L/R` objects exist in
`PUPPET.STYLE.ACCESSORIES`, `parent_type='BONE'`, `parent_bone` correct, no vertex groups;
move foot IK control and verify accessory follows

### Tests for User Story 2 ⚠️ Write FIRST, ensure FAIL

- [X] T015 [P] [US2] Blender contract tests in `tests/blender/test_accessories.py`: accessory objects exist with `acc.*` names in `PUPPET.STYLE.ACCESSORIES`; `parent == rig`, `parent_type='BONE'`, `parent_bone` matches `attach_bone`; no vertex groups; no Armature modifier; removal deletes object + orphaned mesh data
- [X] T016 [US2] Accessory-following test in `tests/blender/test_accessories.py`: translate `foot_ctrl.L` and verify evaluated `acc.shoe.*.L` world position moved with the foot while `.R` stayed

### Implementation for User Story 2

- [X] T017 [US2] Implement `AccessorySpec` + `ACCESSORY_CATALOG` (≥3 shoe styles, ≥3 hat styles per SC-002) in `src/puppet_pipeline/styling/accessories.py`: each spec = 1–4 primitives (`box|cylinder|sphere`) with per-primitive kind, scale, offset; allowed `attach_bone` sets (`foot.L`/`foot.R` shoes, `head` hats)
- [X] T018 [US2] Implement `AccessoryBuilder.build(spec, side=None)` in `src/puppet_pipeline/styling/accessories.py`: create primitives via `from_pydata`/primitive ops, join into single `acc.*` object, `parent_type='BONE'` to `rig` with `matrix_parent_inverse` placing it at rest pose, link only into `PUPPET.STYLE.ACCESSORIES`; scale ∝ `limb_thickness` read from the source generation manifest's parameters (fall back to `0.10` if absent)
- [X] T019 [US2] Implement `AccessoryBuilder.remove(name)` in `src/puppet_pipeline/styling/accessories.py`: delete object + unused mesh datablock; warn-no-op if name unknown
- [X] T020 [US2] Wire `--accessory <style>` / `--accessory <style>:<bone>` CLI flags in `style_puppet.py`; shoes auto-expand to both feet unless a side is given

**Checkpoint**: US1+US2 both work — materials and accessories independently

---

## Phase 5: User Story 3 — Change Background Scene (Priority: P3)

**Goal**: Swap in procedural 2D silhouette scenarios behind the puppet

**Independent Test**: Apply `playground`; `bg.*` objects appear at `depth_y > 0` in
`PUPPET.STYLE.BACKGROUND` while puppet is unchanged; `clear` removes all `bg.*`

### Tests for User Story 3 ⚠️ Write FIRST, ensure FAIL

- [X] T021 [P] [US3] Blender contract tests in `tests/blender/test_backgrounds.py`: build scenario → all objects named `bg.*` in `PUPPET.STYLE.BACKGROUND`; every prop mesh Y-dimension ≈ 0 (planar); all objects share `depth_y` plane; `clear()` removes every `bg.*` and leaves collection empty
- [X] T022 [P] [US3] Catalog tests in `tests/blender/test_backgrounds.py`: ≥5 scenarios exist (`kitchen`, `playground`, `office`, `room`, `bathroom`); each yields ≥2 props + ground/horizon bands

### Implementation for User Story 3

- [X] T023 [US3] Implement `PropSpec` + `BackgroundSpec` + `BACKGROUND_CATALOG` (5 scenarios) in `src/puppet_pipeline/styling/backgrounds.py`: `sky_color`, `ground_color`, `horizon_z`, `depth_y` (default 1.5), `props: list[PropSpec]` with `kind|position(x,z)|scale(x,z)|color`
- [X] T024 [US3] Implement `BackgroundBuilder.build(spec)` + `clear()` in `src/puppet_pipeline/styling/backgrounds.py`: flat `bg.*` meshes at fixed +Y depth, `mat.*` flat colors, exclusive linking to `PUPPET.STYLE.BACKGROUND`, deterministic rebuild (replace existing `bg.*` on re-apply)
- [X] T025 [US3] Wire `--background <scenario>` / `--no-background` CLI flags in `style_puppet.py`

**Checkpoint**: US1–US3 all functional — complete styled scene possible

---

## Phase 6: User Story 4 — Preview Before Applying (Priority: P4)

**Goal**: Non-destructive PNG previews of any styling choice under `build/previews/`

**Independent Test**: Request material preview → PNG written, scene `.blend` byte-identical,
no persistent `mat.*`/`acc.*`/`bg.*` changes

### Tests for User Story 4 ⚠️ Write FIRST, ensure FAIL

- [X] T026 [P] [US4] Blender preview tests in `tests/blender/test_preview.py`: `--preview material=blue` writes `build/previews/material-blue.png` (non-empty PNG); scene object count and material datablock set identical before/after; render settings restored
- [X] T027 [P] [US4] Preview coverage test in `tests/blender/test_preview.py`: preview renders for a material, an accessory, and a background all produce distinct PNG files under `build/previews/`

### Implementation for User Story 4

- [X] T028 [US4] Implement `PreviewRenderer` in `src/puppet_pipeline/styling/preview.py`: apply styling choice to scene, set render engine via `try/except` engine assignment (`BLENDER_WORKBENCH` preferred), frame puppet bounds with existing or temporary camera, render PNG, restore engine/resolution/camera and undo styling state
- [X] T029 [US4] Wire `--preview <kind>=<name>` (repeatable) and `--preview-dir` CLI flags in `style_puppet.py`; preview mode MUST NOT save `.blend` or emit manifest

**Checkpoint**: US1–US4 — users can preview anything before committing

---

## Phase 7: User Story 5 — Save and Reset Styling (Priority: P5)

**Goal**: Persist complete styling state to JSON and restore puppet to unstyled defaults

**Independent Test**: Apply full styling → `--save-preset` → `--reset` → re-apply saved preset
→ identical `.styling.json` state both times

### Tests for User Story 5 ⚠️ Write FIRST, ensure FAIL

- [X] T030 [P] [US5] Round-trip tests in `tests/blender/test_styling_presets.py`: style all features → save preset → validate against `preset.schema.json` → reset → apply saved preset → `.styling.json` manifests byte-identical
- [X] T031 [P] [US5] Reset-completeness test in `tests/blender/test_styling_presets.py`: after reset, zero `acc.*`/`bg.*` objects, zero Wireframe modifiers, zero `mat.*` materials, `PUPPET.STYLE` tree removed, geometry/rig/weights identical to pre-styling state

### Implementation for User Story 5

- [X] T032 [US5] Implement `StylingPreset.apply(preset)` and `reset()` in `src/puppet_pipeline/styling/presets.py`: apply orchestrates materials → accessories → background; reset removes all styling objects/materials/modifiers and the `PUPPET.STYLE` tree, preserving base scene
- [X] T033 [US5] Wire `--preset`, `--save-preset`, `--reset` CLI flags in `style_puppet.py`; emit `<name>.styling.json` manifest on every applied (non-preview) run via `StylingManifestWriter`

**Checkpoint**: All 5 user stories independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, stage-boundary audit, documentation

- [X] T034 Styling smoke test in `tests/blender/test_styling_smoke.py`: full pipeline (load → materials → accessories → background → save .blend + styling.json) < 60 s; assert single material application < 10 s (SC-001); second run idempotent (no `.001`, no duplicate collections); zero actions/keyframes/drivers created; invalid preset exits nonzero with no partial outputs
- [X] T035 [P] Complete `style_puppet.py --help` coverage and docstrings for all `styling/` public APIs
- [X] T036 Run full test suite (`pytest tests/unit` + `tests/blender/run_in_blender.py`); fix all failures
- [X] T037 Execute all 5 `quickstart.md` scenarios end-to-end; record actual outputs
- [X] T038 Stage-boundary audit: diff `src/puppet_pipeline/styling/` and `style_puppet.py` — must contain zero armature-structure, mesh-topology, weight, keyframe, action, or driver mutations on existing `pup.*`/`rig` objects beyond material slots and Wireframe modifiers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001 first, T002–T004 in parallel after
- **Foundational (Phase 2)**: T005 blocks T010+; T006–T008 parallel after T005; T009 after T005
- **US1–US5 (Phase 3–7)**: All depend on Phase 2; US1/US2/US3 are mutually independent; US4 (preview) needs at least one styling feature to preview — recommend after US1; US5 needs all apply paths — recommend last
- **Polish (Phase 8)**: After all desired stories

### Parallel Opportunities

- T002, T003, T004 — independent test files
- T006, T007, T008 — independent modules (same dir, different concerns)
- T010, T011 — two test files
- T015, T016 — one file but sequential sections (not marked both [P])
- T017+T023 — different modules; US2/US3 phases could run fully in parallel
- T030, T031 — same file, sequential

## Implementation Strategy

### MVP First (US1 Only)

1. Phase 1 + Phase 2 → foundation
2. Phase 3 (US1 materials) → **STOP and VALIDATE**: color any part, toggle fill mode
3. Demo-ready: `--material torso=blue` works end-to-end

### Incremental Delivery

US1 → US2 → US3 → US4 → US5, each independently testable; US4/US5 are capability layers
over the earlier stories.

## Notes

- [P] tasks touch different files/modules with no ordering requirement
- Constitution: tests written red first; Blender ops via `bpy` only; node lookup by `type`;
  no localized names; no external assets; schema-v1 generation manifest untouched
- Commit after each task or logical group; stop at checkpoints to validate independently
