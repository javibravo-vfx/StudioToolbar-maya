# Studio Toolbar for Maya

[![Maya](https://img.shields.io/badge/Maya-2022%2B-37A5CC)](https://www.autodesk.com/products/maya/) ![Version](https://img.shields.io/badge/version-0.1.11-informational) ![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white) ![Qt](https://img.shields.io/badge/PySide-6%20%7C%202-41CD52?logo=qt&logoColor=white) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-555) [![Studio Toolbar](https://img.shields.io/badge/also%20for-3ds%20Max%20%C2%B7%20Houdini%20%C2%B7%20Blender-6a4fb6)](https://github.com/javibravo-vfx/StudioToolbar-max)

Pipeline toolbar for Maya, docked right under the Shelf: project / sequence / shot / task
navigation, versioned open and save, project paths and render output — with the same folder
rules, config, look and Setup as [Studio Toolbar for MAX](https://github.com/javibravo-vfx/StudioToolbar-max),
Houdini and [Blender](https://github.com/javibravo-vfx/StudioToolbar-blender).

Maya 2022+ (tested with 2027) · version 0.1.11 · Author: Javi Bravo (VFX)

![Studio Toolbar for Maya](docs/toolbar.png)

```
<root>/<prefix><PROJECT>/<SEQ>/<PROJECT>_<SHOT>/3D/<TASK>/1_projects | 2_review | 3_publish
e.g.  T:\VFX-MOR\010\MOR_010_0010\3D\6_animation\1_projects\MOR_010_0010_animation_v003.ma
```

## What's in the bar

| Control | What it does |
|---|---|
| **PROJECT / SEQ / SHOT / TASK** | Dropdowns filled from disk, same filters as Max. The last selection is shared with Max, Houdini and Blender. |
| Project | Maya's **Set Project**: the workspace goes to `<root>/<prefix>XXX/3D` (asks to create `3D` if it's missing; writes a default `workspace.mel` if there's none). |
| **+** | Creates a missing task folder with its subfolders (from the Setup). |
| **Folder** | Opens the shot, the task or any of its subfolders in the file browser. |
| **OPEN ▾** | File dialog that starts in the task's scenes folder · ▾ recent versions of the task. Asks to save changes first. |
| **SAVE ▾** | Save dialog with the next version ready (`<shot>_<task>_v###.ma`) · ▾ saves the next version in one click. Keeps the scene's type (`.ma` / `.mb`). |
| **GET** | Fills the dropdowns from the open scene. Turns amber when the scene is in another shot/task. Runs by itself when a scene is opened. |
| **PATHS** | Max's Set Paths, as Maya file rules (see below). |
| **SET RENDER** | Render output → `3_publish/<name>_v###/` (see below). |
| **SHOT NAME** | Names renders after the dropdowns instead of the scene. |
| **RESET** | File rules back to Maya's defaults. |
| **Status** | Last action, fixed width · click for the history (click a line to copy its path). |
| **⚙** | Pipeline Setup, shared with Max, Houdini and Blender. |

### PATHS

| Maya file rule | Folder |
|---|---|
| `scene` | `task/1_projects` |
| `sourceImages` | `task/1_projects/textures` |
| `movie` (playblasts) | `task/2_review` |
| `images` (renders) | `task/3_publish` |
| `alembicCache` · `fileCache` · `diskCache` | `task/1_projects/cache/…` — only if the task has a `cache` folder |

They're stored inside the scene (`fileInfo`) and restored when it's opened — only if the scene is
still in the same shot/task; a scene copied to another shot turns PATHS amber instead. They're
never written to `workspace.mel`.

### SET RENDER

Same rules as Max:

- `defaultRenderGlobals.imageFilePrefix` → `publish/<name>_v###/<name>_v###`, 4-digit frames, with the
  Setup's separator (`_0001` or `.0001`).
- The **version** is always the open scene's; the **name** is the scene's, or `<shot>_<task>` with
  **SHOT NAME** on — to render several shots from one scene.
- If that version already has renders it asks: **Overwrite / New version / Cancel**.
- Several renderable layers → `<RenderLayer>` subfolders.
- With Arnold loaded, the output driver is set to EXR.

## Install

1. Copy this repo to the studio share as `T:\.studio-toolbar\maya\` (next to `max\`, `houdini\` and `blender\`).
2. Copy `modules\StudioToolbar.mod` to `Documents\maya\modules\` — or set
   `MAYA_MODULE_PATH=T:/.studio-toolbar/maya/modules` for the whole studio — and restart Maya.
   (The `.mod` points to `T:/.studio-toolbar/maya`; edit it if your share is elsewhere.)
3. Once, in the Script Editor's **Python** tab (no spaces before the line):

   ```python
   import studiotoolbar_maya; studiotoolbar_maya.install_shelf()
   ```

   It creates a **StudioToolbar** shelf tab with the **STM** button. Running it again is safe.
4. **STM** docks the toolbar under the Shelf, at full width; clicking it again removes it. If Maya
   is closed with the toolbar open, it comes back by itself on the next start.

Works with PySide6 (Maya 2025+) and PySide2.

### Notes

- **OPEN and SAVE use the operating system's file dialog.** SAVE needs it to pre-fill the next
  version's name, and it's faster on network drives.
- **Freezes when browsing files** (in Maya's own File ▸ Open too) usually come from a **mapped
  network drive that's disconnected or slow**: Maya's dialog waits for every drive before showing
  anything. Disconnect stale drives in *This PC*, or set *Preferences ▸ Interface ▸ Open/Save
  dialog* to **OS native**.

## Shared config

Everything lives in `~/.studio-toolbar/` and is shared with Max, Houdini and Blender:

| File | Contents |
|---|---|
| `pipeline_config.ini` | Root, prefix, tasks, subfolders… (the Setup). Keys this toolbar doesn't use are kept. |
| `pipeline_presets.json` | Named Setup presets. |
| `pipeline_state.ini` | Last Project / Sequence / Shot / Task and SHOT NAME. |

On a machine where the projects aren't under `T:`, set the environment variable `STM_ROOT` to the
folder that holds the `VFX-XXX` projects — it's never written to the shared config.

## Repository

```
modules/StudioToolbar.mod      Maya module (adds scripts/ to the Python path)
scripts/studiotoolbar_maya.py  toolbar, docking, PATHS, SET RENDER, shelf installer
scripts/stm_pipeline.py        shared pipeline rules (same module as Houdini / Blender)
scripts/stm_qt.py              shared Qt look + Pipeline Setup dialog (same as Houdini)
dev/test_maya.py               tests without Maya: fake maya.cmds + real PySide6
dev/make_tree.py               fake pipeline folder tree for the tests
```

Run the tests with `pip install PySide6-Essentials` then
`QT_QPA_PLATFORM=offscreen python dev/test_maya.py`.

`stm_pipeline.py` and `stm_qt.py` are shared with the Houdini toolbar; change them in both places together.
