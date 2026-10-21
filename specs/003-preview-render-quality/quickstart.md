# Quickstart: Preview Render Quality

Validate each scenario end-to-end against a generated puppet at
`build/puppet.blend` (with its `build/puppet.manifest.json` sibling).

## 1. EEVEE-lit preview

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet.blend --preview material=blue
```

Verify: `build/previews/material-blue.png` shows shaded limbs, a contact
shadow under the character, and the console logs no EEVEE warning (or a
`Warning: EEVEE unavailable; fell back to Workbench` line on Workbench).

## 2. Toon outlines

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet.blend --output build/puppet-styled.blend \
  --material torso=blue --outline --outline-thickness 0.03 \
  --preview material=blue
```

Verify: every `pup.*` object in `puppet-styled.blend` has an `outline_toon`
SOLIDIFY modifier with `use_flip_normals` and an appended `mat.outline` slot;
the PNG shows a dark stroke around the torso. Manifest records
`schema: styling-v2` with a resolved `outline` object.

## 3. Custom outline color + preset round-trip

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet-styled.blend --outline --outline-color red \
  --save-preset build/toon.json
```

Verify: `build/toon.json` has `schema: styling-preset-v2` and
`outline.color` serialized as `#d32f2f`. Loading it back reproduces the look:

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet.blend --preset build/toon.json
```

## 4. Richer props + resolution

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet-styled.blend --preview background=playground \
  --preview-resolution 1280x720 --render-resolution 1920x1080
```

Verify: `background-playground.png` is exactly 1280×720; the slide reads as
ladder + ramp in two tones; the saved blend's `scene.render` is
`BLENDER_EEVEE_NEXT` at 1920×1080 and the manifest `render` block matches.

## 5. Mutual exclusion + reset

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet-styled.blend --fill-mode outline --outline
```

Verify: warning `fill-mode outline overrides toon outline` prints, exit 0,
no `outline_toon` modifiers created. Then:

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet-styled.blend --reset
```

Verify: zero `outline_toon` modifiers remain, `mat.outline` datablocks
removed, scene returns to base state.
