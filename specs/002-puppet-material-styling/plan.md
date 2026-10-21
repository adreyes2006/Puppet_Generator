# Implementation Plan: Puppet Material and Accessory Styling

**Branch**: `feature/puppet-material-styling` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-puppet-material-styling/spec.md`

## Summary

A new `styling` pipeline stage consumes a generated puppet `.blend` (from feature 001) and applies
visual customization: per-part materials, procedural accessories (shoes, hats), and procedural 2D
silhouette backgrounds. A new entrypoint script (`style_puppet.py`) runs inside Blender headlessly,
accepts either CLI flags or a JSON styling preset, writes PNG previews to `build/previews/`, and
emits a separate `<name>.styling.json` manifest that does not touch the schema-v1 generation
manifest. Styling is a fourth pipeline stage added by this spec — it modifies appearance only and
never alters geometry, armature, or creates animation data.

## Technical Context

**Language/Version**: Python 3.13 (interpreter bundled with Blender 5.2.2 LTS); minimum Blender 4.2

**Primary Dependencies**: `bpy`, `bpy.data`, `mathutils` (`Vector`), `json`, `argparse`,
`dataclasses`, `pathlib` — all stdlib/Blender bundled; no third-party packages.

**Storage**: Files only — `<name>.styling.json` manifest, styling preset JSON files, PNG previews
under `build/previews/`.

**Testing**: `pytest` for pure-Python units (preset schema, catalog validation, naming) and
Blender-in-process contract/smoke tests via `blender --background --python tests/blender/run_in_blender.py`.

**Target Platform**: Windows/Linux/macOS with Blender 4.2+; validated on Blender 5.2.2 LTS;
headless CI via `blender --background`.

**Project Type**: CLI tool / DCC automation script.

**Performance Goals**: Styling application < 30 s; preview render < 60 s per image (headless
EEVEE/Workbench).

**Constraints**: Strict stage separation per constitution; deterministic procedural geometry
(seedless but parameter-driven); stable naming; no external assets; schema-v1 manifest immutable;
no animation data.

**Scale/Scope**: One new `styling/` package (~5 modules), one new CLI entrypoint, two new JSON
schemas (preset, styling manifest), 10+ material presets, 3 shoe + 3 hat styles, 5 backgrounds.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Python-first, headless | PASS | New entrypoint `style_puppet.py`; all ops via `bpy`; runnable with `--background` |
| II. Stage separation | PASS* | Styling is a NEW stage required by the spec; it consumes generation output via the .blend + naming contract and never writes into generation/rigging internals. See Complexity Tracking. |
| III. Blender MCP rules | PASS | Material colors set on Principled BSDF node inputs; node lookup by `type`; no localized names (research.md) |
| IV. Deterministic artifacts | PASS | All geometry procedural (clarified in spec); preset JSON records full styling state; stable naming v1 extension |
| V. Test-first validation | PASS | Contract tests on material assignment, accessory parenting, styling manifest schema, preset round-trip |
| VI. Simplicity / YAGNI | PASS | Procedural primitives only; JSON presets; no plugin/asset system |

\* Stage addition justified in Complexity Tracking.

**Post-design re-check (2026-10-17)**: PASS. The data model, contracts (`styling.schema.json`,
`preset.schema.json`, `styling-naming.md` v1.1), and quickstart all preserve stage separation —
styling consumes the puppet `.blend` via the naming contract only, never modifies schema-v1 or
geometry/rig internals, and creates no animation data. All seven research decisions are
constitution-compliant (node-type lookups, procedural assets only, no localized names).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Fourth pipeline stage (`styling/`) | Spec explicitly requires material/accessory/background customization, which fits none of the three constitutional stages | Folding into `generation/` would mix appearance logic into geometry generation, violating stage purity; it is a new stage, not a merge — separation is preserved |

## Architecture Overview

```text
style_puppet.py               # CLI entrypoint: argparse → orchestrate styling stages → save .blend + styling.json
src/puppet_pipeline/
├── common/                   # (existing, unchanged)
├── generation/               # (existing, unchanged)
├── rigging/                  # (existing, unchanged)
├── verify/                   # (existing, unchanged)
└── styling/
    ├── naming.py             # Styling naming constants (v1.1): PUPPET.STYLE collections, acc./bg./mat. prefixes
    ├── scene.py              # setup_style_collections() + validate_puppet_scene()
    ├── materials.py          # MaterialCatalog + MaterialApplier: presets, fill modes, per-part assignment
    ├── accessories.py        # AccessoryBuilder: procedural shoes/hats, bone parenting, attach/detach
    ├── backgrounds.py        # BackgroundBuilder: procedural 2D silhouette scenes, swap/clear
    ├── presets.py            # StylingPreset: JSON load/save/reset, complete styling state round-trip
    ├── preview.py            # PreviewRenderer: offscreen PNG renders to build/previews/
    └── manifest.py           # StylingManifestWriter: schema-v1 styling.json emission
tests/
├── unit/                     # pytest: preset schema, catalog counts, naming
└── blender/                  # contract + smoke tests inside Blender
contracts/
├── styling.schema.json       # styling.json manifest schema
├── preset.schema.json        # styling preset file schema
└── styling-naming.md         # naming v1 extension for style objects/materials/collections
```

### Styling Pipeline Flow

```text
Load puppet .blend (validate rig + 14 parts exist)
      ↓
MATERIALS   → assign material presets per part; toggle solid/outline mode
      ↓
ACCESSORIES → generate + parent shoes/hats to foot/head bones
      ↓
BACKGROUND  → build procedural silhouette scene behind puppet (Y+ depth)
      ↓
OUTPUT      → save .blend + <name>.styling.json
      ↓
(optional) PREVIEW → render PNG to build/previews/ without saving
```

### Class Design

**`styling/materials.py`**
- `MaterialPreset` — frozen dataclass: `name`, `base_color` (RGBA), `roughness`, `metallic`,
  `emission_color`, `emission_strength`, `fill_mode` (`solid | outline`).
- `MaterialCatalog` — static registry of ≥10 presets: matte colors, skin tones, metallic, glowing.
- `MaterialApplier.apply(object_name, preset_name)` — creates/reuses `mat.*` material datablock,
  sets Principled BSDF inputs by `type` lookup, assigns to object; `set_fill_mode(mode)` adds or
  removes Wireframe modifiers on all 14 parts (outline mode) — modifier lives on geometry, not
  shader (spec clarification B).

**`styling/accessories.py`**
- `AccessorySpec` — frozen dataclass: `name`, `style`, `attach_bone`, `offset`, `scale`,
  `part_params` (primitive kind + dimensions).
- `AccessoryBuilder.build(spec)` — creates `acc.*` mesh from primitives (box/cylinder/sphere
  composed via bmesh-style union or object join), parents to `rig` bone via
  `parent_type='BONE'`, inserts into `PUPPET.STYLE.ACCESSORIES` collection.
- `AccessoryBuilder.remove(name)` — deletes accessory object + unused mesh data, restores defaults.

**`styling/backgrounds.py`**
- `BackgroundSpec` — frozen dataclass: `name`, `horizon_z`, `sky_color`, `ground_color`,
  `props: list[PropSpec]` (flat primitive shapes: kind, position, scale, color).
- `BackgroundBuilder.build(spec)` — creates `bg.*` flat meshes at fixed `y > 0` depth behind the
  XZ puppet plane, inserts into `PUPPET.STYLE.BACKGROUND`; `clear()` removes all `bg.*` objects.
- Catalog: kitchen, playground, office, room, bathroom (minimum 5 per SC-002).

**`styling/presets.py`**
- `StylingPreset` — dataclass mirroring `preset.schema.json`: `materials` (part→preset map),
  `fill_mode`, `accessories` (list), `background`, `seed` (optional).
- `save(path)`, `load(path)`, `reset()` — reset removes all `mat.*` assignments beyond defaults,
  all `acc.*`/`bg.*` objects, and Wireframe modifiers; restores each part's original material.

**`styling/preview.py`**
- `PreviewRenderer.render(name, out_dir)` — configures camera/frame covering puppet bounds,
  renders Workbench or EEVEE still to `build/previews/<name>.png`, restores prior render settings;
  scene state after preview is identical to before (non-destructive).

**`styling/manifest.py`**
- `StylingManifestWriter.write(path, state)` — emits deterministic JSON per
  `contracts/styling.schema.json`: active material map, fill mode, accessories, background,
  Blender version, source puppet manifest reference.

## Project Structure

### Documentation (this feature)

```text
specs/002-puppet-material-styling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist (exists)
├── contracts/
│   ├── styling.schema.json
│   ├── preset.schema.json
│   └── styling-naming.md
└── tasks.md             # /speckit.tasks output (not created here)
```

### Source Code (repository root)

```text
src/puppet_pipeline/styling/
├── __init__.py
├── naming.py
├── scene.py
├── materials.py
├── accessories.py
├── backgrounds.py
├── presets.py
├── preview.py
└── manifest.py
style_puppet.py
tests/unit/test_styling_presets.py
tests/unit/test_material_catalog.py
tests/blender/test_materials.py
tests/blender/test_accessories.py
tests/blender/test_backgrounds.py
tests/blender/test_styling_smoke.py
```

**Structure Decision**: New `styling/` package alongside existing `generation/`, `rigging/`,
`verify/` — mirrors the stage-per-package convention established in feature 001. New top-level
`style_puppet.py` entrypoint parallels `generate_puppet.py`.
