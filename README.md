# FeatureHighlight

A FreeCAD addon. Select a PartDesign feature in the tree and see what it does to the model,
without making it visible or double-clicking it into edit mode.

| Selected in the tree | Highlighted |
|---|---|
| Pad, Revolution, additive loft/pipe/primitive | the added material, transparent green |
| Pocket, Groove, Hole, subtractive loft/pipe/primitive | the removed material, transparent red |
| Linear/Polar Pattern, Mirrored, MultiTransform | the difference to the previous feature: added green, removed red |
| Fillet, Chamfer, Draft, Thickness | the edges/faces they act on, orange |
| Sketch | its geometry, yellow |

The highlight is drawn on top of the model (x-ray), so material hidden inside the part is visible too.
It is purely visual: it can't be clicked and never becomes part of the document.
Picking faces or edges in the 3D view does not trigger it, only selecting whole objects in the tree does.
Features inside Parts and bodies shown through Links are highlighted where they actually appear.

## Install

**Addon Manager** (recommended):
Edit → Preferences → Addon Manager → Custom repositories → add
`https://github.com/KargJonas/FeatureHighlight` with branch `main`.
Then install *FeatureHighlight* from the Addon Manager and restart FreeCAD.

**Manually:** clone this repository into your FreeCAD `Mod` folder
(`~/.local/share/FreeCAD/v1-1/Mod/` on Linux for FreeCAD 1.1, see `App.getUserAppDataDir()`) and restart FreeCAD:

```sh
git clone https://github.com/KargJonas/FeatureHighlight ~/.local/share/FreeCAD/v1-1/Mod/FeatureHighlight
```

## Use

Highlighting is on after installing. Toggle it with **V, H** or the *Feature Highlight* toolbar button in
the PartDesign workbench. The setting is remembered across sessions.

Requires FreeCAD 1.1 or newer.

## License

LGPL-2.1-or-later, the same as FreeCAD.
