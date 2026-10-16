# Changelog

## 0.1.11
- No empty strip under the toolbar after closing and re-opening it: the extra room Maya gives the
  re-created dock goes back to the viewports.
- The STM button removes and rebuilds the dock instead of hiding it; tab row hidden, exact bar height.
- OPEN uses the OS file dialog (like SAVE).
- Lighter background check (every 2 s, only when something changed, nothing when hidden).
- Setup: previews debounced, project scan cached per root/prefix — no freeze on network drives.
- `install_shelf()` creates its own **StudioToolbar** shelf tab.

## 0.1.0
- First Maya version: dock under the Shelf, Set Project, + task, folders, OPEN ▾ / SAVE ▾ with
  versions, GET, PATHS as file rules (kept in the scene), SET RENDER + SHOT NAME, RESET,
  Pipeline Setup shared with Max / Houdini / Blender.
