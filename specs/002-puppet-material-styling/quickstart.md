# Quickstart: Puppet Material and Accessory Styling

**Feature**: `specs/002-puppet-material-styling`

Validation scenarios proving the styling stage works end-to-end. All commands run headlessly;
the puppet must be generated first (feature 001).

## Prerequisites

```powershell
# Generate a base puppet (required input)
blender --background --factory-startup --python generate_puppet.py -- \
  --output build/default-puppet.blend \
  --manifest build/default-puppet.manifest.json

# Unit tests (no Blender needed)
python -m pytest tests/unit
```

## Scenario 1 — Apply a single material (US1)

```powershell
blender --background --factory-startup --python style_puppet.py -- \
  --input build/default-puppet.blend \
  --material torso=blue \
  --output build/styled-puppet.blend \
  --styling-manifest build/styled.styling.json
```

**Expected**: `styled-puppet.blend` opens with a blue torso; `styled.styling.json` validates
against `contracts/styling.schema.json` and lists `pup.torso → blue`.

## Scenario 2 — Full styling from preset (US1+US2+US3)

```powershell
blender --background --factory-startup --python style_puppet.py -- \
  --input build/default-puppet.blend \
  --preset presets/example-preset.json \
  --output build/styled-preset.blend \
  --styling-manifest build/styled-preset.styling.json
```

**Expected**: all preset materials, accessories (`acc.*` objects parented to foot/head bones),
and background (`bg.*` objects behind the puppet) are applied; manifest reflects the full state.

## Scenario 3 — Preview without applying (US4)

```powershell
blender --background --factory-startup --python style_puppet.py -- \
  --input build/default-puppet.blend \
  --preview material=blue \
  --preview background=playground \
  --preview-dir build/previews/
```

**Expected**: `build/previews/material-blue.png` and `build/previews/background-playground.png`
exist; input `.blend` is byte-identical to before (non-destructive preview).

## Scenario 4 — Save and reset (US5)

```powershell
# Style, save preset, then reset
blender --background --factory-startup --python style_puppet.py -- \
  --input build/styled-preset.blend \
  --save-preset presets/my-look.json --reset \
  --output build/reset-puppet.blend
```

**Expected**: `presets/my-look.json` validates against `contracts/preset.schema.json`;
`reset-puppet.blend` contains no `acc.*`/`bg.*` objects, no Wireframe modifiers, and no `mat.*`
materials beyond defaults — identical geometry/rig to the pre-styling puppet.

## Scenario 5 — Repeat styling (idempotence)

Run Scenario 1 twice against the same input.

**Expected**: identical `.styling.json` bytes both times; no `.001` suffixed objects, materials,
or collections; no duplicate `PUPPET.STYLE` collections.

## Automated contract tests

```powershell
blender --background --factory-startup --python tests/blender/run_in_blender.py -- \
  --tests tests/blender/test_materials.py tests/blender/test_accessories.py \
          tests/blender/test_backgrounds.py tests/blender/test_styling_smoke.py
```

**Expected**: all styling tests pass — material assignment, accessory bone parenting, background
silhouette generation, preview PNG output, preset round-trip, and reset completeness.
