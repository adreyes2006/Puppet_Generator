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

## Future goals

- Colored materials and visual styles
- Eyes, eyebrows, mouth, and facial expressions
- Walk cycles, idle animations, and gestures
- A library of reusable character presets

## Status

This repository is under initial development. The first milestone is a working generator that produces a rigged 2D puppet in Blender.
