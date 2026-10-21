# Implementation Plan: Preview Render Quality

**Branch**: `feature/preview-render-quality` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Upgrade the styling preview path from flat Workbench renders to EEVEE lighting,
add persistent configurable inverted-hull outlines on `pup.*`/`acc.*` objects,
enrich background props with multi-tone sub-primitives, and add
`--preview-resolution` / `--render-resolution` flags. Schema bump to
`styling-preset-v2` / `styling-v2` with v1 read compatibility.

## Technical Context

**Language/Version**: Python 3.11+ inside Blender (`bpy`)
**Primary Dependencies**: Blender ≥4.2 (`BLENDER_EEVEE_NEXT`), existing
`puppet_pipeline.styling` package, no new external deps
**Storage**: JSON presets/manifests (v2), `.blend` scene state
**Testing**: `pytest` (unit, no bpy) + `tests/blender/run_in_blender.py`
(unittest in-Blender); CI on Ubuntu + xvfb + Mesa
**Target Platform**: Windows/Linux, headless Blender 4.2–5.2
**Constraints**: deterministic output, context-free data API (no `bpy.ops`
where avoidable), non-destructive previews, stage separation preserved

## Constitution Check

- ✅ Python + Blender MCP — all work inside `bpy`, exercised via MCP/CLI
- ✅ Stage separation — changes confined to `styling/` package +
  `style_puppet.py`; no generation/rigging/animation modules touched
- ✅ Determinism — fixed light rig, seeded-free catalog, byte-stable manifests
- ✅ No animation data — modifiers/materials only; zero keyframes/drivers

## Project Structure

### Documentation (this feature)

```text
specs/003-preview-render-quality/
├── spec.md                  # requirements + 12 clarifications
├── plan.md                  # this file
├── research.md              # engine/outline/schema decisions
├── data-model.md            # OutlineSpec, RenderProfile, SubPropSpec
├── contracts/
│   ├── styling-preset-v2.schema.json
│   └── styling-v2.schema.json
├── checklists/requirements.md
└── quickstart.md            # 5 end-to-end scenarios
```

### Source changes

```text
src/puppet_pipeline/styling/
├── outline.py        # NEW — OutlineSpec, parse helpers, OutlineApplier
├── render.py         # NEW — RenderProfile, engine fallback, light rig,
│                     #      resolution parsing, blend render-settings apply
├── preview.py        # MOD — EEVEE-first engine order, resolution param,
│                     #      light rig + world in snapshot/restore
├── presets.py        # MOD — v2 emit + v1/v2 load, outline field,
│                     #      reset_styling removes hulls
├── manifest.py       # MOD — styling-v2 emit, outline + render fields,
│                     #      v1 read helper
├── backgrounds.py    # MOD — SubPropSpec, joined multi-primitive prop mesh,
│                     #      richer catalog entries
└── materials.py      # MOD — color parsing helper reuse (name-or-hex)

style_puppet.py       # MOD — 5 new CLI flags, warning path, render
                      #      settings persisted to saved blend

tests/unit/
├── test_outline.py        # NEW
├── test_render.py         # NEW
├── test_presets_v2.py     # NEW
└── test_manifest_v2.py    # NEW

tests/blender/
├── test_outline_apply.py    # NEW — hull modifiers, materials, idempotence,
│                            #      reset, fill-mode precedence
├── test_render_engine.py    # NEW — EEVEE/fallback, light rig, resolution,
│                            #      PNG pixel sampling for outline
└── test_backgrounds.py      # MOD — sub-prop composition assertions
```

## Phase Overview

| Phase | Scope |
|-------|-------|
| 1 Setup | New modules + failing tests scaffolded |
| 2 Foundational | `OutlineSpec`/`RenderProfile` types, color/resolution parsers, schema v2 dataclasses |
| 3 US1 EEVEE | Engine order flip, light rig, snapshot/restore extension, blend render settings |
| 4 US2 Outlines | `OutlineApplier`, materials, CLI flags, preset/manifest wiring, reset |
| 5 US3 Rich props | `SubPropSpec`, joined-mesh builder, catalog enrichment |
| 6 US4 Resolution | `--preview-resolution`/`--render-resolution` + validation |
| 7 Polish | v1→v2 migration tests, pixel-sampling test, quickstart validation |

## Complexity Tracking

No constitution violations. Outline stays a Solidify modifier — no new object
type, no Freestyle.
