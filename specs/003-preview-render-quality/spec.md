# Feature Specification: Preview Render Quality

**Feature Branch**: `feature/preview-render-quality`
**Created**: 2026-10-17
**Status**: Draft
**Input**: Improve preview/render quality so generated previews look like a polished
2D cartoon: real lighting, bold outlines on characters and props, richer multi-tone
background props, and higher-resolution output — while staying fully headless and
deterministic.

## Clarifications

### Session 2026-10-17

- Q: Which render engine replaces Workbench for styled previews? → A: `BLENDER_EEVEE_NEXT`
  with Workbench kept as fallback via try/except engine assignment.
- Q: Which outline technique gives the bold cartoon stroke? → A: Geometry-based
  inverted-hull outline (Solidify modifier, flipped normals, black material) —
  deterministic, headless-safe, works in EEVEE and Workbench. Freestyle rejected:
  render-pipeline-dependent and harder to validate in tests.
- Q: Do outlines apply to the puppet only or also props/accessories? → A: Puppet body
  parts and accessories get outlines; background props stay flat silhouettes.
- Q: Are outlines persistent styling state or a preview toggle? → A: Persistent —
  part of the styling state stored in presets and the styling manifest, applied to
  the blend file, and removed by `--reset` like other styling.
- Q: How do schemas carry `outline`? → A: Bump both to v2 — `styling-preset-v2` adds
  an `outline` object and `styling-v2` manifests record it; v1 files remain readable
  via a compatibility path.
- Q: Do render settings apply to previews only or the saved blend too? → A: Both —
  previews render with EEVEE + chosen resolution, and the styled `.blend` stores the
  same engine/resolution so interactive renders match previews.
- Q: How do `--outline` and `--fill-mode outline` interact? → A: Mutually exclusive —
  `--fill-mode outline` wins, a warning is emitted, and the toon outline is skipped
  for that run (preset `outline` is honored only when `fill_mode` is `solid`).
- Q: Are outline thickness and color configurable? → A: Yes — `--outline-thickness`
  and `--outline-color` CLI flags plus `outline` object fields in
  `styling-preset-v2` (`{enabled, thickness, color}`); defaults derive thickness
  from `limb_thickness` and use near-black.
- Q: What color formats does `--outline-color` accept? → A: Either a material
  catalog preset name or an `#rrggbb` hex string; presets serialize to hex.
- Q: What resolution does the saved `.blend` store? → A: A separate
  `--render-resolution` flag defaulting to `1920x1080`; `--preview-resolution`
  remains preview-only with its own `640x480` default.
- Q: How do multi-primitive richer props manifest? → A: One joined mesh per prop —
  `bg.prop.<name>` naming and clear semantics unchanged; the catalog declares
  extra primitives with per-primitive color and offset.
- Q: What units does `--outline-thickness` use? → A: Absolute Blender units,
  defaulting to `limb_thickness × 0.15`; scales with the puppet automatically.
- Q: What light rig does EEVEE use? → A: World ambient (light gray) plus a
  single angled Sun lamp for soft shading and contact shadows; a fixed,
  deterministic setup created by the preview renderer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lit, shaded preview renders (Priority: P1)

As a user, I want previews rendered with real lighting so the puppet reads as a 3D
character instead of flat blocks of color.

**Why this priority**: Core of the quality upgrade; without EEVEE nothing else
(shadows, tone) is possible.

**Independent Test**: Render `--preview material=blue`; assert the PNG is written and
`scene.render.engine` during render was `BLENDER_EEVEE_NEXT` (or Workbench fallback
logged when unavailable).

**Acceptance Scenarios**:

1. **Given** a generated puppet, **When** `--preview material=blue` runs on a machine
   with EEVEE, **Then** the PNG shows shaded limbs with ambient occlusion and a contact
   shadow under the character.
2. **Given** EEVEE unavailable, **When** a preview renders, **Then** the run falls back
   to Workbench and still produces a valid PNG.

---

### User Story 2 - Bold cartoon outlines (Priority: P2)

As a user, I want the puppet rendered with dark outlines so it reads like a cartoon
character.

**Why this priority**: The signature visual element of the reference style; needs P1's
engine but is separately testable.

**Independent Test**: Enable outlines via `--outline` (or a preset's `outline`
field); assert each `pup.*` and `acc.*` object carries an outline modifier and the
rendered PNG shows a dark stroke.

**Acceptance Scenarios**:

1. **Given** outlines enabled, **When** a preview renders, **Then** every body part and
   accessory shows a continuous dark outline.
2. **Given** outlines disabled, **When** a preview renders, **Then** output matches the
   previous flat look (backward compatibility).
3. **Given** outline mode active, **When** `--reset` runs, **Then** outline modifiers
   are removed along with other styling.

---

### User Story 3 - Richer background props (Priority: P3)

As a user, I want background props built from multiple tones/shapes so scenarios read
more like scenes than flat colored rectangles.

**Why this priority**: Polish; improves visual quality without changing pipeline
structure.

**Independent Test**: Each catalog scenario yields props composed of ≥2 primitives or
≥2 tones, still planar on the shared depth plane.

**Acceptance Scenarios**:

1. **Given** the playground scenario, **When** it builds, **Then** the slide shows a
   ladder + ramp in two tones rather than one flat rect.
2. **Given** any scenario, **When** it builds, **Then** all prop vertices remain on the
   prop's own +Y depth plane (still silhouette-based).

---

### User Story 4 - Configurable render resolution (Priority: P4)

As a user, I want to set preview resolution so previews are usable as presentation
images.

**Why this priority**: Trivial flag; lowest value but cheap.

**Independent Test**: `--preview-resolution 1920x1080` produces a PNG of exactly that
size.

**Acceptance Scenarios**:

1. **Given** `--preview-resolution 1280x720`, **When** a preview renders, **Then** the
   PNG is 1280×720 and the default remains 640×480 when the flag is absent.

---

### Edge Cases

- EEVEE requested but unavailable → warn, fall back to Workbench, exit 0.
- Outline modifier on an already-outlined object → idempotent, no duplicates.
- Invalid resolution string (`720p`, `axb`) → clear CLI error, no partial outputs.
- `--outline` + `--fill-mode outline` combined → mutually exclusive; `--fill-mode
  outline` wins, warning emitted, toon outline skipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preview rendering MUST attempt `BLENDER_EEVEE_NEXT` first and fall back
  to `BLENDER_WORKBENCH` on `TypeError`/engine-unavailable errors.
- **FR-002**: The system MUST provide an optional outline style applying an
  inverted-hull outline to every `pup.*` and `acc.*` object via a modifier, with
  configurable thickness and color (`--outline`, `--outline-thickness`,
  `--outline-color`, preset `outline` object). Thickness is in absolute Blender
  units (default `limb_thickness × 0.15`); `--outline-color` accepts a material
  catalog preset name or `#rrggbb` hex, serialized to hex in presets/manifests.
- **FR-003**: Outline modifiers MUST be removed by `--reset` and excluded from the
  base geometry manifest (styling-only artifacts).
- **FR-004**: Background props MAY compose multiple primitives/tones while remaining
  planar silhouette meshes on the scenario depth plane; each prop stays a single
  joined mesh under its existing `bg.prop.<name>` identity.
- **FR-005**: The CLI MUST accept `--preview-resolution WxH` with validation;
  default stays 640×480.
- **FR-005a**: The CLI MUST accept `--render-resolution WxH` defaulting to
  `1920x1080`, stored into the saved styled `.blend` alongside the EEVEE engine
  so interactive renders match the configured output quality.
- **FR-005b**: EEVEE renders MUST use a fixed deterministic light rig: world
  ambient light plus one angled Sun lamp (soft shading, contact shadows),
  created and removed/restored by the preview renderer like other render state.
- **FR-006**: Rendering changes MUST NOT introduce animation data, external assets,
  or mutations outside the styling stage.
- **FR-007**: All existing preview tests MUST keep passing (non-destructive restore,
  PNG naming, scene unchanged after render).

### Key Entities

- **RenderProfile**: engine preference, preview resolution, render (saved-blend)
  resolution, light rig, outline on/off, outline color/thickness.
- **OutlineSpec**: `{enabled, thickness, color}` — persisted in `styling-preset-v2`
  and `styling-v2`; defaults: thickness = `limb_thickness × 0.15` (absolute
  Blender units), color near-black, serialized as `#rrggbb`.
- **Enhanced PropSpec**: adds optional `sub_props` (child primitives composing one
  prop, each with its own color and offset, joined into a single mesh).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Preview PNG under EEVEE renders in under 60s headless.
- **SC-002**: With outlines on, a pixel-sampling check finds dark outline pixels adjacent
  to filled body-part pixels in the rendered PNG.
- **SC-003**: Every existing scenario still builds all required props with ≥2 visual
  components after the richer-prop pass.
- **SC-004**: Outline on/off produces visually distinct PNGs (byte-different, both valid).
- **SC-005**: `--reset` removes every outline modifier and restores pre-styling state.
- **SC-006**: Zero external asset dependencies; all geometry remains procedural.

## Assumptions

- EEVEE exists in Blender ≥4.2 as `BLENDER_EEVEE_NEXT`; fallback keeps CI safe.
- The outline uses a Solidify-based inverted hull (subtractive thickness,
  `use_flip_normals`, black emission material) rather than Freestyle.
- CI runs under xvfb so EEVEE renders use Mesa software GL; SC-001 bound accounts for
  software rendering.
