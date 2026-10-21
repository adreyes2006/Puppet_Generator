# Tasks: Preview Render Quality

**Input**: `specs/003-preview-render-quality/{spec,plan,research,data-model}.md` + `contracts/`
**Prerequisites**: plan.md complete; feature 002 merged into develop
**Tests**: included (constitution requires verification; test-first per phase)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US4) this task belongs to
- File paths are relative to repo root

---

## Phase 1: Setup

**Purpose**: Scaffold new modules + failing test files

- [x] T001 [P] Create `src/puppet_pipeline/styling/outline.py` skeleton (`OutlineSpec` dataclass, `OutlineApplier` stub) with module docstring
- [x] T002 [P] Create `src/puppet_pipeline/styling/render.py` skeleton (`RenderProfile` dataclass, engine/light-rig stubs)
- [x] T003 [P] Create failing unit test `tests/unit/test_outline.py` (spec defaults, color parse: catalog name, hex, invalid)
- [x] T004 [P] Create failing unit test `tests/unit/test_render.py` (resolution parse `WxH`, bounds, invalid strings; profile defaults)

**Checkpoint**: `pytest tests/unit` — new tests fail (import errors expected)

---

## Phase 2: Foundational

**Purpose**: Shared types/parsers all stories depend on — MUST complete first

- [ ] T005 Implement `OutlineSpec` in `outline.py`: frozen dataclass `{enabled, thickness, color}`; `DEFAULT_OUTLINE_COLOR = "#0d0d0d"`; `THICKNESS_FACTOR = 0.15`; `resolve(limb_thickness)` → concrete `{thickness, color}`
- [ ] T006 Implement `parse_outline_color(value)` in `outline.py`: `#rrggbb` passthrough (validated), catalog name → hex via `MATERIAL_CATALOG`, else `ValueError`
- [ ] T007 Implement `parse_resolution(value)` in `render.py`: `r"^(\d+)x(\d+)$"`, bounds 16–16384, `ValueError` on bad input; `RenderProfile` dataclass with defaults (EEVEE, 640×480, 1920×1080)
- [ ] T008 Extend `StylingState` in `manifest.py` with `outline: dict | None` + `render: dict | None`; emit `schema: styling-v2` with both fields in `build()`; add `STYLING_SCHEMA_V1` constant + v1-accepting `read()` helper
- [ ] T009 Extend `StylingPreset` in `presets.py`: `PRESET_SCHEMA_V1/V2` constants, `outline: OutlineSpec | None` field, `from_dict` accepts both schemas (v1 → `outline=None`), `to_dict`/`serialize` emit v2 with `outline` object; update `_TOP_LEVEL_KEYS`

**Checkpoint**: `pytest tests/unit` all green; T003/T004 now pass

---

## Phase 3: User Story 1 — EEVEE rendering (P1)

**Goal**: Previews render with real lighting; saved blend stores EEVEE + resolution

- [ ] T010 [US1] Write Blender test `tests/blender/test_render_engine.py`: engine recorded during render is EEVEE-or-WarnedWorkbench; light rig objects (`preview_sun`, world ambient) exist during render and are removed after; scene render settings fully restored
- [ ] T011 [US1] Implement `RenderProfile.apply_engine(scene)` in `render.py`: try `BLENDER_EEVEE_NEXT`, except `TypeError` → `BLENDER_WORKBENCH` + return warning string; `setup_light_rig(scene)` creates world ambient + `preview_sun` SUN lamp (energy 2.0, angle 0.5, ~30° tilt); `teardown_light_rig` removes created datablocks
- [ ] T012 [US1] Update `preview.py` `_render_to`: use `RenderProfile` engine order (EEVEE first), call `setup_light_rig` when engine is EEVEE; extend `_snapshot`/`_restore` to capture world color/strength, lights list, and tear down rig (guarded `hasattr` on `scene.eevee` AO attrs)
- [ ] T013 [US1] Implement `RenderProfile.apply_to_blend(scene)` in `render.py`: sets engine + `render_resolution` on the styled blend; call from `style_puppet.py` `main()` before `save_as_mainfile`; record result in `StylingState.render` for the manifest

**Checkpoint**: `--preview material=blue` renders via EEVEE on capable hosts; T010 passes; existing preview tests still green

---

## Phase 4: User Story 2 — Toon outlines (P2)

**Goal**: Persistent configurable inverted-hull outlines on `pup.*` + `acc.*`

- [ ] T014 [US2] Write Blender test `tests/blender/test_outline_apply.py`: `outline_toon` SOLIDIFY modifier on each `pup.*`/`acc.*` with `use_flip_normals`, negative offset, `use_even_offset`, `material_offset` → appended `mat.outline` slot; idempotent re-apply; `reset_styling()` removes modifiers + slots + `mat.outline` datablock; `--fill-mode outline` + outline → warning, no modifiers
- [ ] T015 [US2] Implement `OutlineApplier` in `outline.py`: `apply(obj, spec)` creates `outline_toon` SOLIDIFY modifier (skip if present); `apply_all(spec, limb_thickness)` iterates `pup.*` via `GEOMETRY_BINDINGS` + `acc.*` objects; `remove_all()` for reset; `_outline_material()` creates/reuses `mat.outline` with emission
- [ ] T016 [US2] Update `reset_styling()` in `presets.py`: remove `outline_toon` modifiers from `pup.*`/`acc.*`, pop trailing `mat.outline` slots, purge `mat.outline` datablocks
- [ ] T017 [US2] Update `StylingPreset.apply()` in `presets.py`: honor `outline` field only when `fill_mode == "solid"`; resolved spec passed to `OutlineApplier.apply_all`
- [ ] T018 [US2] Add CLI flags to `style_puppet.py`: `--outline`, `--outline-thickness`, `--outline-color`; merge preset outline with flag precedence (flags override preset fields); emit warning + skip when `fill_mode == "outline"`; include resolved `outline` in `StylingState` + `save_preset`

**Checkpoint**: quickstart scenario 2 + 5 pass; T014 green; `--fill-mode outline` + `--outline` warns and skips

---

## Phase 5: User Story 3 — Richer props (P3)

**Goal**: Multi-tone multi-primitive props, still single `bg.prop.<name>` meshes

- [ ] T019 [US3] Extend `test_backgrounds.py`: assert each catalog prop has ≥2 primitives or ≥2 tones after enrichment; assert all vertices share the prop's `prop_y`; assert sub-props add material slots to the same mesh
- [ ] T020 [US3] Add `SubPropSpec` + `PropSpec.sub_props` in `backgrounds.py`; implement `_composite_prop_mesh(prop, prop_y)` merging rect/circle primitives via `from_pydata` with index offsets and per-face `material_index`; update `BackgroundBuilder.build` to append all sub-prop materials to one object
- [ ] T021 [US3] Enrich `BACKGROUND_CATALOG`: ≥2 primitives/tones per prop in all 5 scenarios (e.g., slide = ladder + ramp + legs; swing = frame + chains + seat; fridge = body + door + handle)

**Checkpoint**: `pytest tests/unit` + `tests/blender/test_backgrounds.py` green; `bg.prop.*` count and names unchanged

---

## Phase 6: User Story 4 — Resolution flags (P4)

**Goal**: `--preview-resolution` and `--render-resolution` wired through

- [ ] T022 [US4] Add `--preview-resolution` (default `640x480`) + `--render-resolution` (default `1920x1080`) to `style_puppet.py` parser; validate via `parse_resolution`; `StylingError` (exit 2) on bad input
- [ ] T023 [US4] Thread `preview_resolution` into `PreviewRenderer.render()` → `_render_to` instead of hardcoded 640/480; Blender test asserts PNG dimensions match requested size

**Checkpoint**: `--preview-resolution 1280x720` yields a 1280×720 PNG; defaults unchanged; `--render-resolution` lands in saved blend + manifest `render` block (from T013)

---

## Phase 7: Polish & Validation

**Purpose**: v1 compat proof, pixel-sampling, full suite, quickstart

- [ ] T024 [P] Unit test `tests/unit/test_presets_v2.py`: v1 preset loads with `outline=None`; v2 round-trips outline; unknown outline keys rejected; invalid color/thickness → `PresetError`
- [ ] T025 [P] Unit test `tests/unit/test_manifest_v2.py`: v2 emit includes `outline`/`render`; v1 manifest readable via `read()`; determinism (byte-identical re-serialize)
- [ ] T026 Blender test: pixel-sampling check — render outline preview, read PNG via `bpy.data.images.load`, assert dark pixels adjacent to fill pixels (SC-002); assert outline-on vs outline-off PNGs differ (SC-004)
- [ ] T027 Update `README.md`: document new CLI flags, v2 schemas, EEVEE behavior, outline customization examples
- [ ] T028 Run full suite: `pytest tests/unit` + `tests/blender/run_in_blender.py` — all green
- [ ] T029 Execute all 5 quickstart scenarios; record results in quickstart verification

---

## Dependencies

```text
Phase 1 (T001-T004) → Phase 2 (T005-T009)
    Phase 2 → Phase 3 (US1) ─┐
    Phase 2 → Phase 4 (US2) ─┼→ Phase 7
    Phase 2 → Phase 5 (US3) ─┤
    Phase 2 → Phase 6 (US4) ─┘
    Phases 3-6 parallelizable after Phase 2
```

## Task Count: 29

| Phase | Tasks | Story |
|-------|-------|-------|
| 1 Setup | T001–T004 | — |
| 2 Foundational | T005–T009 | — |
| 3 | T010–T013 | US1 |
| 4 | T014–T018 | US2 |
| 5 | T019–T021 | US3 |
| 6 | T022–T023 | US4 |
| 7 Polish | T024–T029 | — |

## Independent Test Criteria

- **US1**: `--preview material=blue` → EEVEE PNG with shading/shadow; Workbench fallback warns + still renders
- **US2**: `--outline` → `outline_toon` modifiers + dark stroke in PNG; `--reset` removes all; fill-mode precedence warning
- **US3**: each scenario's props ≥2 primitives/tones; `bg.prop.<name>` count/names unchanged
- **US4**: `--preview-resolution WxH` → PNG exactly WxH; `--render-resolution` stored in blend + manifest

## Implementation Strategy

**MVP**: Phases 1–4 (US1 + US2) — the visible quality jump. US3/US4 are additive polish that can land in any order afterward.

**Per-phase commits** (matching feature-002 workflow): one commit per phase on `feature/preview-render-quality`, tests green before each commit, no pushes until requested.
