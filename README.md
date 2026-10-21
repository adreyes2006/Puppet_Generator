# 2D Puppet Generator

A Blender automation project that creates a customizable 2D stick-figure character and prepares it for animation.

## What is this?

This project writes Python scripts that run inside Blender. Instead of manually modeling a character, you run a command and Blender automatically builds a complete puppet: body parts, bones, and controls that let you move it.

## What is it for?

The generated puppet can be used for:

- 2D animations and short videos
- Game characters
- Educational or explainer content
- Social media animated characters
- Learning how procedural character generation works

## Why automate it?

Manually creating and rigging a character is repetitive. This project makes it:

- **Repeatable** — same parameters always produce the same puppet
- **Customizable** — change arm length, torso size, thickness, and other proportions
- **Testable** — automated tests verify that generation, rigging, and movement work correctly
- **Expandable** — later stages can add facial features, colors, and animation controllers

## How it works (planned)

```
Input parameters
      ↓
Generate body parts (head, torso, arms, legs)
      ↓
Build skeleton and controls
      ↓
Bind geometry to the skeleton
      ↓
Output: .blend file + manifest
      ↓
Future: styling, facial rigging, animation
```

## What the puppet will look like

A simple 2D stick-figure with:

- Head and torso
- Two arms with forearms and hands
- Two legs with thighs, shins, and feet
- Controls to grab and move hands and feet
- Controls to bend elbows and knees
- A root control to move the whole character

## Styling the puppet

`style_puppet.py` applies materials, accessories, backgrounds, toon outlines,
and renders previews — all non-destructively:

```bash
blender --background --factory-startup --python style_puppet.py -- \
  --input build/puppet.blend --output build/puppet-styled.blend \
  --material torso=blue --accessory sneakers --background playground \
  --outline --outline-thickness 0.03 --outline-color "#101010" \
  --preview material=blue --preview-resolution 1280x720
```

- **Outlines** (`--outline`) use an inverted-hull Solidify modifier on body
  parts and accessories. Customize with `--outline-thickness` (Blender units,
  default `limb_thickness × 0.15`) and `--outline-color` (catalog name or
  `#rrggbb`). Mutually exclusive with `--fill-mode outline` (wireframe wins).
- **Rendering**: previews use EEVEE with a fixed sun + ambient light rig,
  falling back to Workbench with a warning when EEVEE is unavailable.
  `--render-resolution WxH` (default `1920x1080`) is stored on the saved blend.
- **Presets**: `styling-preset-v2` adds an `outline` object
  (`{enabled, thickness, color}`); v1 presets still load. Styling manifests are
  `styling-v2` (adds `outline` + `render`); v1 manifests remain readable.

## Future goals

- Eyes, eyebrows, mouth, and facial expressions
- Walk cycles, idle animations, and gestures
- A library of reusable character presets

## Status

Active development. Feature 001 (generation + rigging) and feature 002
(materials, accessories, backgrounds, previews) are merged; feature 003 adds
EEVEE rendering, toon outlines, richer props, and resolution controls.
