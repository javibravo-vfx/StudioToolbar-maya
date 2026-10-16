# -*- coding: utf-8 -*-
"""
Studio Toolbar for MAYA — pipeline navigation
Author: Javi Bravo (VFX)

Same folder rules, config, look and Setup dialog as Studio Toolbar for MAX / Houdini
(~/.studio-toolbar/pipeline_config.ini and pipeline_presets.json are shared).

  PROJECT            sets the Maya project (workspace) to <root>/<prefix>XXX/3D  (asks to create 3D)
  SEQ / SHOT / TASK  dropdowns, filled from disk
  +                  create a missing task folder (with its subfolders)
  folder             open shot / task / subfolders in the file browser
  OPEN ▾             browse the task's scenes · arrow: recent versions
  SAVE ▾             save dialog with the next version name · arrow: one-click next version
  GET                fill the dropdowns from the open scene (amber when they differ)
  PATHS              point the project's file rules to the task (like Max's Set Paths), kept in the scene
  SET RENDER         render output → publish/<name>_v###/  (version from the scene, like Max)
  SHOT NAME          name renders after the dropdowns instead of the scene
  RESET              file rules back to Maya's defaults
  ⚙                  Pipeline Setup (shared with Max / Houdini / Blender)

show() docks it under the Shelf as a workspace control; Maya restores it on the next start.
"""

import os, re, sys, json, base64

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:                                   # Maya ≤ 2024
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

from maya import cmds, mel
from maya import OpenMayaUI as omui

def _add_core_path():
    """stm_pipeline.py / stm_qt.py live next to this file in the deployed folder
    (T:/.studio-toolbar/maya/scripts). In the repo they come from ../../core."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (here, os.path.normpath(os.path.join(here, "..", "..", "core"))):
        if os.path.isfile(os.path.join(c, "stm_pipeline.py")):
            if c not in sys.path: sys.path.insert(0, c)
            return
_add_core_path()
import stm_pipeline as P
import stm_qt as Q

VERSION      = "0.1.11"
SCENE_EXTS   = (".ma", ".mb")
WC_NAME      = "StudioToolbarWorkspaceControl"
FILEINFO_KEY = "stm_paths"
STATUS_WIDEST = "Render set · 12 nodes (selected)"   # same width as Houdini

# PATHS: Max project paths → Maya file rules
#   scene → scene · image → sourceImages · preview → movie (playblasts)
#   renderoutput → images · cache rules → scenes/cache (only if the task has it)
DEFAULT_RULES = {
    "scene": "scenes", "sourceImages": "sourceimages", "movie": "movies", "images": "images",
    "alembicCache": "cache/alembic", "fileCache": "cache/nCache", "diskCache": "data",
}

C_OK, C_ERR, C_WARN, C_DIM = Q.C_OK, Q.C_ERR, Q.C_WARN, Q.C_DIM

def bar_height():
    """Exact height of the bar: one row of controls + a thin margin."""
    return Q.H() + Q.S(6)


# ── Maya helpers ──────────────────────────────────────────────────────────────
def _fwd(p):
    return p.replace("\\", "/") if p else p

def _scene_path():
    try:
        return cmds.file(q=True, sceneName=True) or ""
    except Exception:
        return ""

def _main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None

def _workspace_root():
    try:
        return os.path.normpath(cmds.workspace(q=True, rootDirectory=True))
    except Exception:
        return ""

def _stored_paths():
    try:
        raw = cmds.fileInfo(FILEINFO_KEY, q=True)
        raw = raw[0] if isinstance(raw, (list, tuple)) else raw
        return json.loads(base64.b64decode(raw).decode("utf-8")) if raw else None
    except Exception:
        return None

def _store_paths(data):
    # base64: fileInfo escapes quotes differently between .ma and .mb
    cmds.fileInfo(FILEINFO_KEY, base64.b64encode(json.dumps(data).encode("utf-8")).decode("ascii"))

def _clear_stored_paths():
    try: cmds.fileInfo(remove=FILEINFO_KEY)
    except Exception: pass

def _apply_rules(rules):
    for k, v in rules.items():
        try: cmds.workspace(fileRule=[k, _fwd(v)])
        except Exception as e: print(f"[STM Paths] {k}: {e}")


class StudioToolbarMaya(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stm_root")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet(Q.toolbar_style())
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.state = P.load_state()
        self._status_log = []
        self._declined_3d = set()
        self._jobs = []
        self._stored_cache = _stored_paths()        # refreshed on open / PATHS / RESET, not every tick
        self._base = P.pipeline_base(_scene_path() or None)
        self._build_ui()
        if not self.get_from_file(quiet=True):       # an open pipeline scene wins over the last selection
            self._populate_projects()
        self._register_jobs()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._update_attention)
        self._timer.start(2000)
        self._update_attention(force=True)

    # ── UI (same order and look as Max / Houdini) ─────────────────────────────
    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        row_w = QtWidgets.QWidget()
        L = QtWidgets.QHBoxLayout(row_w)
        L.setContentsMargins(Q.S(12), Q.S(3), Q.S(12), Q.S(3)); L.setSpacing(Q.S(2))
        self.setFixedHeight(bar_height())
        outer.addWidget(row_w)

        L.addWidget(Q.section_label("PIPELINE")); L.addSpacing(Q.S(6))
        self.project_cb = Q.combo(110, "Project — sets the Maya project to the project's 3D folder")
        self.seq_cb     = Q.combo(110, "Sequence folder")
        self.shot_cb    = Q.combo(330, "Shot")
        self.task_cb    = Q.combo(150, "Task / department folder (e.g. 6_animation)")
        for w in (self.project_cb, self.seq_cb, self.shot_cb, self.task_cb):
            L.addWidget(w); L.addSpacing(Q.S(2))
        self.add_btn = Q.mini_btn("plus", "Create a new task folder for the selected shot")
        self.add_btn.clicked.connect(self._show_task_menu)
        self.folder_btn = Q.mini_btn("folder", "Open shot / task folders in the file browser")
        self.folder_btn.clicked.connect(self._show_folder_menu)
        L.addWidget(self.add_btn); L.addSpacing(Q.S(2)); L.addWidget(self.folder_btn)

        Q.section_sep(L)
        self.open_btn, self._open_menu = Q.split_btn(
            "OPEN", "OPEN — browse the scenes in the task folder\n▾ recent versions of this task")
        self.open_btn.clicked.connect(self.open_dialog)
        self._open_menu.aboutToShow.connect(self._fill_open_menu)
        self.save_btn, self._save_menu = Q.split_btn(
            "SAVE", "SAVE — save dialog in the task folder, next version pre-filled\n▾ save next version directly")
        self.save_btn.clicked.connect(self.save_dialog)
        self._save_menu.aboutToShow.connect(self._fill_save_menu)
        self.get_btn = Q.action_btn("GET", self._GET_TIP)
        self.get_btn.clicked.connect(lambda: self.get_from_file())
        self.paths_btn = Q.action_btn("PATHS", self._PATHS_TIP)
        self.paths_btn.clicked.connect(self.set_paths)
        self.render_btn = Q.action_btn("SET RENDER", self._RENDER_TIP)
        self.render_btn.clicked.connect(self.set_render)
        self.shotname_chk = QtWidgets.QCheckBox("SHOT NAME")
        self.shotname_chk.setFixedHeight(Q.H())
        self.shotname_chk.setToolTip(
            "SET RENDER naming\n"
            "  ON  → render named after the dropdowns:  shot_task_v###\n"
            "  OFF → render named after the open scene\n"
            "The version always comes from the scene.\n"
            "Use ON to render several shots from the same scene.")
        self.shotname_chk.setChecked(bool(self.state.get("render_shot_name", False)))
        self.shotname_chk.toggled.connect(lambda on: P.save_state({"render_shot_name": bool(on)}))
        self.reset_btn = QtWidgets.QPushButton("RESET")
        self.reset_btn.setObjectName("reset_btn"); self.reset_btn.setFixedHeight(Q.H())
        self.reset_btn.setToolTip("File rules back to Maya's defaults (the scene stops restoring them)")
        self.reset_btn.clicked.connect(self.reset_paths)
        for b in (self.open_btn, self.save_btn, self.get_btn, self.paths_btn, self.render_btn):
            L.addWidget(b); L.addSpacing(Q.S(6))
        L.addSpacing(Q.S(6)); L.addWidget(self.shotname_chk)
        L.addSpacing(Q.S(10)); L.addWidget(self.reset_btn)

        Q.section_sep(L)
        self.status_lbl = QtWidgets.QLabel()
        self.status_lbl.setObjectName("status_lbl"); self.status_lbl.setTextFormat(QtCore.Qt.RichText)
        self.status_lbl.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.status_lbl.mousePressEvent = lambda e: self._show_status_log()
        self.status_lbl.ensurePolished()
        fm = self.status_lbl.fontMetrics()
        self._status_text_w = fm.horizontalAdvance(STATUS_WIDEST)
        self.status_lbl.setFixedWidth(self._status_text_w + fm.horizontalAdvance("●  ") + Q.S(8))
        L.addWidget(self.status_lbl)
        L.addSpacing(Q.S(8))
        self.setup_btn = Q.mini_btn("gear", "Pipeline Setup — root, prefix, tasks and folder names (shared with Max)")
        self.setup_btn.clicked.connect(self.open_setup)
        L.addWidget(self.setup_btn)
        L.addStretch(1)
        self._paint_status("Ready", C_DIM)

        self.project_cb.currentTextChanged.connect(self._on_project_changed)
        self.seq_cb.currentTextChanged.connect(lambda _: self._populate_shots())
        self.shot_cb.currentTextChanged.connect(lambda _: self._populate_tasks())
        self.task_cb.currentTextChanged.connect(lambda _: self._remember())

    _GET_TIP = "GET — fills Project / Sequence / Shot / Task from the open scene's folder"
    _PATHS_TIP = ("PATHS — point the project's file rules to the task (as Max's Set Paths):\n"
                  "  scene         task / scenes folder\n"
                  "  sourceImages  scenes / textures\n"
                  "  movie         review  (playblasts)\n"
                  "  images        publish (renders)\n"
                  "  caches        scenes / cache  (if the task has it)\n"
                  "Kept inside the scene and restored when it's opened.")
    _RENDER_TIP = ("SET RENDER — render output to the task's publish folder:\n"
                   "  publish / <name>_v### / <name>_v###_####.ext\n"
                   "Version = the open scene's version. Asks before overwriting existing renders.\n"
                   "Several render layers → one subfolder per layer. Arnold output → EXR.")

    # ── status ────────────────────────────────────────────────────────────────
    def _paint_status(self, text, color, detail=None):
        shown = self.status_lbl.fontMetrics().elidedText(text, QtCore.Qt.ElideRight, self._status_text_w)
        esc = shown.replace("&", "&amp;").replace("<", "&lt;")
        self.status_lbl.setText(f'<span style="color:{color}">●</span>&nbsp;{esc}')
        self.status_lbl.setToolTip("\n".join(x for x in (text, detail) if x) + "\n\nClick for history")

    def _set_status(self, text, color=None, detail=None):
        self._paint_status(text, color or C_DIM, detail)
        self._status_log.insert(0, (QtCore.QTime.currentTime().toString("HH:mm:ss"), text, detail or ""))
        del self._status_log[25:]

    def _show_status_log(self):
        m = QtWidgets.QMenu(self)
        if not self._status_log:
            m.addAction("No actions yet").setEnabled(False)
        else:
            Q.menu_header(m, "Last actions — click to copy the path")
        for when, text, detail in self._status_log:
            a = m.addAction(f"{when}   {text}" + (f"      {detail}" if detail else ""))
            if detail:
                a.triggered.connect(lambda c=False, d=detail: QtWidgets.QApplication.clipboard().setText(d))
        m.exec(QtGui.QCursor.pos())

    # ── selection ─────────────────────────────────────────────────────────────
    def sel(self):
        return (self.project_cb.currentText(), self.seq_cb.currentText(),
                self.shot_cb.currentText(), self.task_cb.currentText())

    def _remember(self):
        p, s, sh, t = self.sel()
        if p:
            P.save_state({"project": p, "sequence": s, "shot": sh, "task": t})
            self.state.update(project=p, sequence=s, shot=sh, task=t)

    @staticmethod
    def _fill(cb, items, wanted=None):
        cb.blockSignals(True)
        cb.clear(); cb.addItems(items)
        if wanted and wanted in items: cb.setCurrentText(wanted)
        cb.setEnabled(bool(items))
        cb.blockSignals(False)

    def _populate_projects(self):
        self._fill(self.project_cb, P.list_projects(self._base), self.state.get("project"))
        self._on_project_changed(self.project_cb.currentText())

    def _on_project_changed(self, project):
        self.set_project(project)
        self._populate_sequences()

    def _populate_sequences(self):
        self._fill(self.seq_cb, P.list_sequences(self.project_cb.currentText(), self._base),
                   self.state.get("sequence"))
        self._populate_shots()

    def _populate_shots(self):
        p, s = self.project_cb.currentText(), self.seq_cb.currentText()
        self._fill(self.shot_cb, P.list_shots(p, s, self._base), self.state.get("shot"))
        self._populate_tasks()

    def _populate_tasks(self):
        p, s, sh, _ = self.sel()
        self._fill(self.task_cb, P.list_tasks(p, s, sh, self._base), self.state.get("task"))
        self._remember()

    def _dirs(self):
        p, s, sh, t = self.sel()
        return {
            "shot":    P.shot_dir(p, s, sh, self._base),
            "task":    P.task_dir(p, s, sh, t, base=self._base),
            "scenes":  P.scenes_dir(p, s, sh, t, self._base),
            "review":  P.review_dir(p, s, sh, t, self._base),
            "publish": P.publish_dir(p, s, sh, t, self._base),
            "snap":    P.snapshot_dir(p, s, sh, t, self._base),
        }

    # ── project (= Maya's Set Project) ────────────────────────────────────────
    def project_3d_dir(self, project=None):
        project = project if project is not None else self.project_cb.currentText()
        return os.path.join(P.project_dir(project, self._base), P.DEPT_FOLDER) if project else None

    def set_project(self, project):
        """Maya project = <root>/<prefix><project>/3D. Asks to create 3D when it's missing (like Max).
        A workspace.mel with Maya's default rules is written if the folder has none."""
        if not project: return False
        path_3d = self.project_3d_dir(project)
        if not os.path.isdir(path_3d) and project not in self._declined_3d:
            ans = QtWidgets.QMessageBox.question(self, "Create Structure",
                f"Folder '{P.DEPT_FOLDER}' not found in {project}.\nDo you want to create it?\n\n{_fwd(path_3d)}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if ans == QtWidgets.QMessageBox.Yes:
                try: os.makedirs(path_3d, exist_ok=True)
                except Exception as e: self._set_status("Create 3D error", C_ERR); print(f"[STM] {e}")
            else:
                self._declined_3d.add(project)
        if not os.path.isdir(path_3d):
            return False
        if os.path.normcase(_workspace_root()) == os.path.normcase(os.path.normpath(path_3d)):
            return True
        try:
            cmds.workspace(_fwd(path_3d), openWorkspace=True)
            if not os.path.isfile(os.path.join(path_3d, "workspace.mel")):
                cmds.workspace(saveWorkspace=True)
            self._set_status(f"Project {project}", C_OK, _fwd(path_3d))
            return True
        except Exception as e:
            self._set_status("Set project error", C_ERR); print(f"[STM] set project: {e}")
            return False

    # ── GET ───────────────────────────────────────────────────────────────────
    def get_from_file(self, quiet=False):
        scene = _scene_path()
        info = P.parse_path(scene) if scene else None
        if not info:
            if not quiet: self._set_status("Scene not in pipeline", C_ERR, scene or None)
            return False
        self._base = P.pipeline_base(scene)
        if info["project"] not in P.list_projects(self._base):
            if not quiet: self._set_status("Project not listed", C_ERR)
            return False
        self.state.update(project=info["project"], sequence=info["seq"],
                          shot=info["shot"], task=info["task"] or self.state.get("task"))
        self._fill(self.project_cb, P.list_projects(self._base), info["project"])
        self._on_project_changed(info["project"])
        self._set_status("GET OK", C_OK)
        return True

    def _file_info(self):
        scene = _scene_path()
        return P.parse_path(scene) if scene else None

    def _update_attention(self, force=False):
        if not force and not self.isVisible():
            return                                  # hidden toolbar: zero work
        scene = _scene_path()
        key = (scene, self.sel(), str(self._stored_cache))
        if not force and key == getattr(self, "_att_key", None):
            return                                  # nothing changed since the last tick
        self._att_key = key
        info = P.parse_path(scene) if scene else None
        p, s, sh, t = self.sel()
        get_on = bool(info) and not P.same_place(
            info, {"project": p, "seq": s, "shot": sh, "task": t},
            keys=("project", "seq", "shot") + (("task",) if info.get("task") else ()))
        stored = self._stored_cache
        stale = bool(info and info.get("task") and stored) and not P.same_place(stored, info)
        self._attention(self.get_btn, get_on, self._GET_TIP,
                        "⚠ The open scene is in a different shot/task than the dropdowns")
        self._attention(self.paths_btn, stale, self._PATHS_TIP,
                        "⚠ The paths saved in this scene belong to another shot/task (copied file?)")

    @staticmethod
    def _attention(btn, on, base_tip, warn):
        if bool(btn.property("attention")) == on: return
        btn.setProperty("attention", on)
        btn.style().unpolish(btn); btn.style().polish(btn)
        btn.setToolTip(base_tip + (f"\n\n{warn}" if on else ""))

    # ── scene events ──────────────────────────────────────────────────────────
    def _register_jobs(self):
        try:
            self._jobs.append(cmds.scriptJob(event=["SceneOpened", self._on_scene_opened], protected=True))
        except Exception as e:
            print(f"[STM] scriptJob: {e}")

    def _on_scene_opened(self, *_):
        try:
            self.objectName()
        except RuntimeError:                           # widget gone on the C++ side
            self.cleanup(); return
        self._stored_cache = _stored_paths()
        if self.get_from_file(quiet=True):
            info, stored = self._file_info(), self._stored_cache
            if stored and info and info.get("task"):
                if P.same_place(stored, info):
                    _apply_rules(stored.get("rules", {}))
                    self._set_status("Paths restored", C_OK, stored.get("rules", {}).get("scene"))
                else:
                    self._set_status("Paths skipped — another shot", C_WARN)
        self._update_attention(force=True)

    def cleanup(self):
        for j in self._jobs:
            try:
                if cmds.scriptJob(exists=j): cmds.scriptJob(kill=j, force=True)
            except Exception: pass
        self._jobs = []
        try: self._timer.stop()
        except Exception: pass

    def closeEvent(self, e):
        self.cleanup(); super().closeEvent(e)

    # ── + task ────────────────────────────────────────────────────────────────
    def _show_task_menu(self):
        p, s, sh, _ = self.sel()
        if not all([p, s, sh]):
            self._set_status("Select a shot first", C_ERR); return
        m = QtWidgets.QMenu(self)
        missing = P.missing_tasks(p, s, sh, self._base)
        Q.menu_header(m, "Create task folder")
        if not missing:
            m.addAction("All tasks already exist").setEnabled(False)
        for t in missing:
            m.addAction(t).triggered.connect(lambda c=False, tt=t: self._create_task(tt))
        m.exec(self.add_btn.mapToGlobal(QtCore.QPoint(0, self.add_btn.height())))

    def _create_task(self, task):
        p, s, sh, _ = self.sel()
        try:
            d = P.create_task(p, s, sh, task, self._base)
        except Exception as e:
            self._set_status("Create task error", C_ERR); print(f"[STM] create task: {e}"); return
        self.state["task"] = task
        self._populate_tasks()
        self._set_status("Task created", C_OK, _fwd(d))

    # ── folders ───────────────────────────────────────────────────────────────
    def _show_folder_menu(self):
        d = self._dirs()
        m = QtWidgets.QMenu(self)
        if not d["shot"]:
            m.addAction("Select a shot first").setEnabled(False)
        else:
            def add(label, path):
                a = m.addAction(Q.mini_icon("folder"), label)
                a.setEnabled(bool(path) and os.path.isdir(path))
                a.triggered.connect(lambda c=False, pp=path: P.open_folder(pp))
            Q.menu_header(m, "Open folder")
            add("Shot", d["shot"])
            if d["task"]:
                add("Task", d["task"])
                m.addSeparator()
                for sub in P.subfolders():
                    add(sub, os.path.join(d["task"], sub))
                if d["snap"] and os.path.normpath(d["snap"]) != os.path.normpath(d["review"] or ""):
                    add("Snapshots", d["snap"])
        m.exec(self.folder_btn.mapToGlobal(QtCore.QPoint(0, self.folder_btn.height())))

    # ── open / save ───────────────────────────────────────────────────────────
    def _fill_open_menu(self):
        m = self._open_menu; m.clear()
        folder = self._dirs()["scenes"]
        files = P.list_scenes(folder, SCENE_EXTS)
        if not files:
            m.addAction("No scenes in this task yet").setEnabled(False); return
        Q.menu_header(m, "Recent in this task")
        current = os.path.normcase(os.path.normpath(_scene_path())) if _scene_path() else ""
        for f in files[:12]:
            full = os.path.join(folder, f)
            act = m.addAction(P.describe_file(full))
            if os.path.normcase(os.path.normpath(full)) == current:
                act.setCheckable(True); act.setChecked(True)
            act.triggered.connect(lambda c=False, pp=full: self._load(pp))

    def _load(self, path):
        try:
            if cmds.file(q=True, modified=True) and not mel.eval('saveChanges("")'):
                self._set_status("Cancelled"); return
            cmds.file(_fwd(path), open=True, force=True)
            self._set_status("File loaded", C_OK, _fwd(path))
        except Exception as e:
            self._set_status("Open error", C_ERR); print(f"[STM] open: {e}")

    def open_dialog(self):
        d = self._dirs()
        if not d["scenes"]:
            self._set_status("Select a task first", C_ERR); return
        start = d["scenes"] if os.path.isdir(d["scenes"]) else d["task"]
        # OS file dialog (like SAVE): Maya's own fileDialog2 can hang for a while when it's
        # cancelled with a modified scene, browsing a network folder
        f, _ = QtWidgets.QFileDialog.getOpenFileName(
            _main_window() or self, "Open Maya Scene", _fwd(start),
            "Maya Scenes (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)")
        if f: self._load(f)

    def _scene_ext(self):
        ext = os.path.splitext(_scene_path())[1].lower()
        return ext if ext in SCENE_EXTS else ".ma"

    def _next_path(self):
        p, s, sh, t = self.sel()
        if not all([p, s, sh, t]): return None
        return P.next_scene_path(p, s, sh, t, self._scene_ext(), SCENE_EXTS, self._base)

    def _fill_save_menu(self):
        m = self._save_menu; m.clear()
        nxt = self._next_path()
        if not nxt:
            m.addAction("Select a task first").setEnabled(False); return
        m.addAction(Q.mini_icon("save"), f"Save next version now  →  {os.path.basename(nxt)}") \
         .triggered.connect(self.quick_save)

    def _save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cmds.file(rename=_fwd(path))
        cmds.file(save=True, type="mayaBinary" if path.lower().endswith(".mb") else "mayaAscii")
        m = re.search(r"_v(\d+)\.m[ab]$", os.path.basename(path), re.IGNORECASE)
        self._set_status(f"Saved v{m.group(1)}" if m else "Saved", C_OK, _fwd(path))

    def quick_save(self):
        nxt = self._next_path()
        if not nxt:
            self._set_status("Select a task first", C_ERR); return
        try: self._save(nxt)
        except Exception as e:
            self._set_status("Save error", C_ERR); print(f"[STM] save: {e}")

    def save_dialog(self):
        nxt = self._next_path()
        if not nxt:
            self._set_status("Select a task first", C_ERR); return
        os.makedirs(os.path.dirname(nxt), exist_ok=True)
        filters = "Maya ASCII (*.ma);;Maya Binary (*.mb)"
        first = "Maya Binary (*.mb)" if nxt.endswith(".mb") else "Maya ASCII (*.ma)"
        f, chosen = QtWidgets.QFileDialog.getSaveFileName(_main_window() or self, "Save Maya Scene",
                                                          _fwd(nxt), filters, first)
        if not f: return
        if not f.lower().endswith(SCENE_EXTS):
            f += ".mb" if "mb" in (chosen or "") else ".ma"
        try: self._save(f)
        except Exception as e:
            self._set_status("Save error", C_ERR); print(f"[STM] save: {e}")

    # ── PATHS / RESET (= Max's Set Paths / Reset) ─────────────────────────────
    def path_rules(self):
        p, s, sh, t = self.sel()
        if not all([p, s, sh, t]): return None
        d = self._dirs()
        scenes, psubs = d["scenes"], P.task_projects_subs(t)
        rules = {
            "scene":        scenes,
            "sourceImages": os.path.join(scenes, "textures"),
            "movie":        d["review"],
            "images":       d["publish"],
        }
        if "cache" in psubs:
            cache = os.path.join(scenes, "cache")
            rules.update(alembicCache=os.path.join(cache, "alembic"),
                         fileCache=os.path.join(cache, "nCache"), diskCache=cache)
        return {k: _fwd(v) for k, v in rules.items()}

    def set_paths(self):
        rules = self.path_rules()
        if not rules:
            self._set_status("Select a task first", C_ERR); return
        p, s, sh, t = self.sel()
        try:
            self.set_project(p)
            _apply_rules(dict(DEFAULT_RULES, **rules))     # cache rules back to default if this task has none
            self._stored_cache = {"project": p, "seq": s, "shot": sh, "task": t, "rules": rules}
            _store_paths(self._stored_cache)
            P.save_state({"project": p, "sequence": s, "shot": sh, "task": t})
            self._set_status("Paths set", C_OK, _fwd(self._dirs()["task"]))
        except Exception as e:
            self._set_status("PATH Error", C_ERR); print(f"[STM] set paths: {e}")
        self._update_attention(force=True)

    def reset_paths(self):
        if QtWidgets.QMessageBox.warning(self, "Reset Paths",
                "Reset the project's file rules back to Maya defaults?",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel) != QtWidgets.QMessageBox.Ok:
            return
        _apply_rules(DEFAULT_RULES)
        _clear_stored_paths()
        self._stored_cache = None
        self._set_status("Reset")
        self._update_attention(force=True)

    # ── SET RENDER (= Max's SET RENDER) ───────────────────────────────────────
    @staticmethod
    def _renderable_layers():
        layers = []
        for lyr in cmds.ls(type="renderLayer") or []:
            if ":" in lyr: continue                         # referenced layers
            try:
                if cmds.getAttr(lyr + ".renderable"): layers.append(lyr)
            except Exception:
                pass
        return layers

    def set_render(self):
        p, s, sh, t = self.sel()
        if not all([p, s, sh, t]):
            self._set_status("Select a task first", C_ERR); return
        d = self._dirs()
        sep = P.cfg().get("render_sep", "_")
        prefix, ver, pad = P.render_target(d["publish"], sh, t, os.path.basename(_scene_path()),
                                           self.shotname_chk.isChecked())
        folder_name = f"{prefix}_v{ver:0{pad}d}"
        target = os.path.join(d["publish"], folder_name)
        if os.path.isdir(target) and any(os.scandir(target)):
            box = QtWidgets.QMessageBox(self)
            box.setWindowTitle("Set Render")
            box.setText(f"{folder_name} already has renders.")
            box.setInformativeText("Overwrite them, or render to the next free version?")
            b_over = box.addButton("Overwrite", QtWidgets.QMessageBox.DestructiveRole)
            b_new  = box.addButton("New version", QtWidgets.QMessageBox.AcceptRole)
            box.addButton(QtWidgets.QMessageBox.Cancel)
            box.setDefaultButton(b_new)
            box.exec()
            if box.clickedButton() is b_new:
                folder_name = P.next_free_render_version(d["publish"], prefix, ver, pad)
            elif box.clickedButton() is not b_over:
                self._set_status("Cancelled"); return

        out_dir = _fwd(os.path.join(d["publish"], folder_name))
        layers = self._renderable_layers()
        multi = len(layers) > 1
        image_prefix = f"{out_dir}/<RenderLayer>/{folder_name}_<RenderLayer>" if multi else f"{out_dir}/{folder_name}"
        notes = []
        try:
            os.makedirs(out_dir, exist_ok=True)
            g = "defaultRenderGlobals"
            cmds.setAttr(g + ".imageFilePrefix", image_prefix, type="string")
            cmds.setAttr(g + ".animation", 1)
            cmds.setAttr(g + ".outFormatControl", 0)
            cmds.setAttr(g + ".putFrameBeforeExt", 1)
            cmds.setAttr(g + ".periodInExt", 2 if sep == "_" else 1)      # 2 = name_####.ext · 1 = name.####.ext
            cmds.setAttr(g + ".extensionPadding", 4)
            if multi: notes.append(f"{len(layers)} layers")
            if cmds.objExists("defaultArnoldDriver"):
                cmds.setAttr("defaultArnoldDriver.ai_translator", "exr", type="string")
                notes.append("EXR")
        except Exception as e:
            self._set_status("SET RENDER Error", C_ERR); print(f"[STM Render] {e}"); return
        print(f"[STM Render] {image_prefix}")
        self._set_status(" · ".join(["Render set"] + notes), C_OK, image_prefix)

    # ── setup ─────────────────────────────────────────────────────────────────
    def open_setup(self):
        dlg = Q.PipelineSetupDialog(_main_window() or self, host="Maya", version=VERSION,
                                    scene_label="Scene filename")
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self._base = P.pipeline_base(_scene_path() or None)
            self._declined_3d.clear()
            self._populate_projects()
            self._set_status("Setup saved", C_OK, _fwd(P.CONFIG_PATH))


# ══════════════════════════════════════════════════════════════════════════════
#  Docking — a Maya workspace control right under the Shelf
# ══════════════════════════════════════════════════════════════════════════════
_WIDGET = None
UI_SCRIPT = "import studiotoolbar_maya; studiotoolbar_maya._restore()"

def _restore():
    """uiScript of the workspace control: builds the toolbar inside it.
    Maya also calls this when it restores the layout on startup."""
    global _WIDGET
    ptr = omui.MQtUtil.getCurrentParent()
    parent = wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None
    if _WIDGET is not None:
        try: _WIDGET.cleanup(); _WIDGET.deleteLater()
        except RuntimeError: pass
    _WIDGET = StudioToolbarMaya(parent)
    if parent is not None:
        lay = parent.layout()
        if lay is None:
            lay = QtWidgets.QVBoxLayout(parent)
        # Maya re-runs this every time the control is shown again: drop anything a previous
        # run left in the layout, otherwise the old widgets and spacing pile up
        while lay.count():
            item = lay.takeAt(0)
            old = item.widget()
            if old is not None and old is not _WIDGET:
                try:
                    if hasattr(old, "cleanup"): old.cleanup()
                    old.hide(); old.setParent(None); old.deleteLater()
                except RuntimeError:
                    pass
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        lay.addWidget(_WIDGET)
    _schedule_fit()
    return _WIDGET

def _schedule_fit():
    for ms in (0, 150, 500):                       # Maya settles the dock area in more than one pass
        QtCore.QTimer.singleShot(ms, _fit_and_hide_tabs)

def _fit_and_hide_tabs():
    """Shrink the workspace control to the bar and hide its tab row (only when the
    toolbar is alone in that dock area, so other panels' tabs are never touched).
    Safe to call any number of times: it sets absolute sizes, nothing accumulates."""
    if _WIDGET is None: return
    h = bar_height()
    _hide_tab_bar(h)                               # before sizing: the hidden tab row must not count
    _tidy_splitter(h)
    try:
        cmds.workspaceControl(WC_NAME, e=True, resizeHeight=h)
    except Exception:
        pass
    try:                                           # the control itself never grows past the bar
        ptr = omui.MQtUtil.findControl(WC_NAME)
        if ptr:
            ctrl = wrapInstance(int(ptr), QtWidgets.QWidget)
            ctrl.setMaximumHeight(h)
            if ctrl.layout() is not None:
                ctrl.layout().setContentsMargins(0, 0, 0, 0); ctrl.layout().setSpacing(0)
    except Exception:
        pass

def _dock_tabwidget():
    """The QTabWidget Maya made for our workspace control (child of the layout QSplitter)."""
    try:
        w = _WIDGET
        while w is not None and not isinstance(w.parentWidget(), QtWidgets.QSplitter):
            w = w.parentWidget()
        return w if isinstance(w, QtWidgets.QTabWidget) else None
    except RuntimeError:
        return None

def _tidy_splitter(h):
    """Maya leaves an empty dock area in the layout splitter each time a workspace control
    is removed; those empty areas are the gap under the toolbar. Hide them (only areas with
    no tabs at all), and size our area exactly to the bar."""
    tw = _dock_tabwidget()
    if tw is None: return
    split = tw.parentWidget()
    sizes = split.sizes()                              # snapshot BEFORE touching anything: Qt re-lays out
    idx = split.indexOf(tw)
    tw.setStyleSheet("QTabWidget::pane { border: 0; margin: 0; padding: 0; top: 0px; }")
    stack = tw.findChild(QtWidgets.QStackedWidget)
    if stack is not None:
        stack.setContentsMargins(0, 0, 0, 0)
    for i in range(split.count()):                     # empty areas left by removed controls
        other = split.widget(i)
        if other is not tw and isinstance(other, QtWidgets.QTabWidget) and other.count() == 0 and other.isVisible():
            other.hide()
    # Maya gives a re-created control more room than the bar needs (the gap): hand the
    # extra to the biggest area — the viewports — so the slot is exactly the bar's height
    extra = sizes[idx] - h if idx >= 0 else 0
    if extra > 0:
        big = max((i for i in range(len(sizes)) if i != idx), key=lambda i: sizes[i])
        sizes[idx] = h
        sizes[big] += extra
        split.setSizes(sizes)
    tw.setMaximumHeight(h)

def _hide_tab_bar(h=None):
    """Hide the tab row of the dock area holding the toolbar (only if the toolbar is its
    only tab) and cap that area's height, so the space the tab row used doesn't stay
    empty when the toolbar is closed and shown again."""
    try:
        w = _WIDGET.parentWidget()
    except RuntimeError:
        return True
    for _ in range(8):
        if w is None: break
        for tb in w.findChildren(QtWidgets.QTabBar):
            if tb.count() == 1 and tb.tabText(0).startswith("Studio Toolbar"):
                tb.hide()
                if h:
                    area = tb.parentWidget()               # tab row + page: the whole dock area
                    if area is not None and area.findChildren(StudioToolbarMaya):
                        area.setMaximumHeight(h)
                        area.updateGeometry()
                return True
        w = w.parentWidget()
    return False

def _close():
    """Remove the workspace control completely (not just hide it). Maya keeps the space a
    hidden control used and gives it back with a gap, so the toolbar is always rebuilt fresh
    — exactly like on startup, which lays it out right."""
    global _WIDGET
    if _WIDGET is not None:
        try: _WIDGET.cleanup()
        except RuntimeError: pass
    _WIDGET = None
    if cmds.workspaceControl(WC_NAME, q=True, exists=True):
        try: cmds.workspaceControl(WC_NAME, e=True, close=True)
        except Exception: pass
        try: cmds.deleteUI(WC_NAME)
        except Exception: pass

def show():
    """Shelf button: toggles the toolbar docked under the Shelf."""
    if cmds.workspaceControl(WC_NAME, q=True, exists=True):
        visible = cmds.workspaceControl(WC_NAME, q=True, visible=True)
        _close()
        if visible:
            return None                                # it was on screen: the button closes it
    base = dict(label=f"Studio Toolbar {VERSION}", retain=False, loadImmediately=True,
                uiScript=UI_SCRIPT, initialHeight=bar_height(), heightProperty="fixed",
                widthProperty="free", minimumWidth=True)
    for where in (dict(dockToControl=["Shelf", "bottom"]),       # full width, right under the shelf
                  dict(dockToMainWindow=["top", False]),
                  dict(floating=True)):
        try:
            cmds.workspaceControl(WC_NAME, **base, **where)
            break
        except Exception as e:
            print(f"[STM dock] {list(where)[0]}: {e}")
            if cmds.workspaceControl(WC_NAME, q=True, exists=True):
                cmds.deleteUI(WC_NAME)
    if _WIDGET is None and cmds.workspaceControl(WC_NAME, q=True, exists=True):
        ptr = omui.MQtUtil.findControl(WC_NAME)            # uiScript didn't run yet: build it now
        if ptr:
            parent = wrapInstance(int(ptr), QtWidgets.QWidget)
            w = StudioToolbarMaya(parent)
            (parent.layout() or QtWidgets.QVBoxLayout(parent)).addWidget(w)
            globals()["_WIDGET"] = w
    return _WIDGET

SHELF_NAME = "StudioToolbar"

def install_shelf():
    """Run once: creates a "StudioToolbar" shelf tab with the Studio Toolbar button.
    Safe to run again: it re-uses the tab and never duplicates the button."""
    shelf_top = mel.eval("$tmp = $gShelfTopLevel")
    tabs = cmds.tabLayout(shelf_top, q=True, childArray=True) or []
    if SHELF_NAME not in tabs:
        mel.eval(f'addNewShelfTab "{SHELF_NAME}"')            # Maya saves it with the other shelves
    shelf = f"{shelf_top}|{SHELF_NAME}" if cmds.shelfLayout(f"{shelf_top}|{SHELF_NAME}", exists=True) else SHELF_NAME
    for b in cmds.shelfLayout(shelf, q=True, childArray=True) or []:
        if cmds.shelfButton(b, q=True, exists=True) and \
           cmds.shelfButton(b, q=True, label=True) == "Studio Toolbar":
            cmds.tabLayout(shelf_top, e=True, selectTab=SHELF_NAME)
            return b
    btn = cmds.shelfButton(parent=shelf, label="Studio Toolbar", annotation="Studio Toolbar — pipeline",
                           image="pythonFamily.png", imageOverlayLabel="STM", sourceType="python",
                           command="import studiotoolbar_maya; studiotoolbar_maya.show()")
    cmds.tabLayout(shelf_top, e=True, selectTab=SHELF_NAME)
    try: mel.eval("saveAllShelves $gShelfTopLevel")
    except Exception: pass
    return btn
