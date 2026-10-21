# Naming Contract Extension: Styling (naming v1.1)

**Scope**: Objects, materials, and collections created by the `styling/` stage.
All rules in `specs/001-stick-figure-puppet/contracts/naming.md` (v1) still apply unchanged;
this file only adds new reserved prefixes and collections.

## Collections

| Name | Purpose |
|------|---------|
| `PUPPET.STYLE` | Root collection for all styling output; child of `PUPPET` |
| `PUPPET.STYLE.ACCESSORIES` | Accessory objects (`acc.*`) |
| `PUPPET.STYLE.BACKGROUND` | Background silhouette objects (`bg.*`) |

## Object prefixes

| Prefix | Examples | Rule |
|--------|----------|------|
| `acc.` | `acc.shoe.sneakers.L`, `acc.shoe.sneakers.R`, `acc.hat.cap` | Accessories; bilateral items keep terminal `.L`/`.R`; single items carry no side suffix |
| `bg.` | `bg.ground`, `bg.horizon`, `bg.prop.slide`, `bg.prop.swing` | Background silhouettes; props use `bg.prop.<element>` |

## Material datablocks

| Prefix | Examples | Rule |
|--------|----------|------|
| `mat.` | `mat.blue`, `mat.skin_light`, `mat.metallic` | One datablock per catalog preset, created once and reused across parts |

## Forbidden

- Blender numeric suffixes (`.001`, `.002`) — same rule as naming v1; styling code must
  detect-and-replace or fail loudly rather than accept a duplicated name.
- Names under `anim_` / `PUPPET.ANIMATION` — styling creates no animation data.
- Any new root collections outside `PUPPET.*`.

## Contract version

`styling-naming` is versioned independently: **v1.1** (extends naming v1). Any change to the
reserved prefixes or collection names is a breaking change and must bump this version.
