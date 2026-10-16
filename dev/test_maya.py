"""Fake `maya`, build the real Maya toolbar with PySide6 offscreen, test it and save a PNG.
    python dev/build.py
    QT_QPA_PLATFORM=offscreen python dev/test_maya.py [out_dir]
"""
import os, sys, types, tempfile, json, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
home = tempfile.mkdtemp(); os.environ["HOME"] = home; os.environ["USERPROFILE"] = home
root = tempfile.mkdtemp(); os.environ["STM_ROOT"] = root
sys.path.insert(0, HERE); import make_tree; make_tree.make(root)
os.makedirs(os.path.join(root, "VFX-NEW", "010", "NEW_010_0010"))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

# ── fake maya ─────────────────────────────────────────────────────────────────
S = {"scene": "", "modified": False, "ws": "", "rules": {}, "fileinfo": {}, "attrs": {}, "jobs": {},
     "nodes": {"defaultRenderGlobals", "defaultArnoldDriver"}, "layers": {"defaultRenderLayer": True},
     "saved_fileinfo": {}, "calls": []}
cmds = types.ModuleType("maya.cmds")
def file(*a, **k):
    if k.get("q") and k.get("sceneName"): return S["scene"]
    if k.get("q") and k.get("modified"): return S["modified"]
    if "rename" in k: S["scene"] = k["rename"]; return
    if k.get("save"):
        open(S["scene"], "w").close(); S["saved_fileinfo"][S["scene"]] = dict(S["fileinfo"])
        S["calls"].append(("save", S["scene"], k.get("type"))); return
    if k.get("open"):
        S["scene"] = a[0]; S["fileinfo"] = dict(S["saved_fileinfo"].get(a[0], {}))
        S["calls"].append(("open", a[0]))
        for job in list(S["jobs"].values()): job()
cmds.file = file
def workspace(*a, **k):
    if k.get("q") and k.get("rootDirectory"): return S["ws"] + "/"
    if k.get("openWorkspace"): S["ws"] = a[0].rstrip("/"); S["rules"] = {}; return
    if k.get("saveWorkspace"): open(os.path.join(S["ws"], "workspace.mel"), "w").close(); return
    if "fileRule" in k: S["rules"][k["fileRule"][0]] = k["fileRule"][1]
cmds.workspace = workspace
def fileInfo(*a, **k):
    if k.get("q"): return [S["fileinfo"][a[0]]] if a[0] in S["fileinfo"] else []
    if "remove" in k: S["fileinfo"].pop(k["remove"], None); return
    S["fileinfo"][a[0]] = a[1]
cmds.fileInfo = fileInfo
def scriptJob(**k):
    if "event" in k: n = len(S["jobs"]) + 1; S["jobs"][n] = k["event"][1]; return n
    if "exists" in k: return k["exists"] in S["jobs"]
    if "kill" in k: S["jobs"].pop(k["kill"], None)
cmds.scriptJob = scriptJob
cmds.ls = lambda type=None: list(S["layers"]) if type == "renderLayer" else []
cmds.getAttr = lambda a: S["layers"][a.split(".")[0]] if a.endswith(".renderable") else S["attrs"].get(a)
def setAttr(a, v, **k): S["attrs"][a] = v
cmds.setAttr = setAttr
cmds.objExists = lambda n: n in S["nodes"]
cmds.fileDialog2 = lambda **k: (S["calls"].append(("fileDialog2", k)), None)[1]
cmds.workspaceControl = lambda *a, **k: False
mel = types.ModuleType("maya.mel"); mel.eval = lambda s: 1
omui = types.ModuleType("maya.OpenMayaUI")
omui.MQtUtil = types.SimpleNamespace(mainWindow=lambda: None, getCurrentParent=lambda: None, findControl=lambda n: None)
maya = types.ModuleType("maya"); maya.cmds, maya.mel, maya.OpenMayaUI = cmds, mel, omui
sys.modules.update({"maya": maya, "maya.cmds": cmds, "maya.mel": mel, "maya.OpenMayaUI": omui})

from PySide6 import QtWidgets
app = QtWidgets.QApplication([]); app.setStyle("Fusion")
f = app.font(); f.setPointSizeF(9); app.setFont(f)
QtWidgets.QMessageBox.question = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.Yes)
QtWidgets.QMessageBox.warning = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.Ok)

import studiotoolbar_maya as M
P, Q = M.P, M.Q
ok = 0
def check(c, msg):
    global ok
    assert c, msg; ok += 1
fwd = lambda p: p.replace("\\", "/")

w = M.StudioToolbarMaya(); w.resize(1600, 34); w.show(); app.processEvents()
check(w.project_cb.count() == 3 and w.shot_cb.count() == 3, "dropdowns filled")
check(S["ws"] == fwd(os.path.join(root, "VFX-MOR", "3D")), ("project = workspace 3D", S["ws"]))
check(os.path.isfile(os.path.join(root, "VFX-MOR", "3D", "workspace.mel")), "workspace.mel written")

w.project_cb.setCurrentText("NEW")
check(os.path.isdir(os.path.join(root, "VFX-NEW", "3D")) and S["ws"].endswith("VFX-NEW/3D"), "creates 3D")
w.project_cb.setCurrentText("MOR")

# PATHS → file rules (fx has cache), stored in the scene
w.seq_cb.setCurrentText("010"); w.shot_cb.setCurrentText("MOR_010_0010"); w.task_cb.setCurrentText("7_fx")
w.set_paths()
base = fwd(os.path.join(root, "VFX-MOR", "010", "MOR_010_0010", "3D", "7_fx"))
check(S["rules"]["scene"] == base + "/1_projects" and S["rules"]["sourceImages"] == base + "/1_projects/textures"
      and S["rules"]["movie"] == base + "/2_review" and S["rules"]["images"] == base + "/3_publish", S["rules"])
check(S["rules"]["alembicCache"] == base + "/1_projects/cache/alembic", "fx cache rules")
check(M._stored_paths()["shot"] == "MOR_010_0010", "stored in fileInfo")

# SAVE next version (.ma by default) → paths travel with the scene
w.quick_save()
saved = S["calls"][-1][1]
check(saved.endswith("MOR_010_0010_fx_v001.ma") and S["calls"][-1][2] == "mayaAscii", S["calls"][-1])
check("Saved v001" in w.status_lbl.text(), w.status_lbl.text())
w.quick_save(); check(S["scene"].endswith("_v002.ma"), S["scene"])

# reopen → GET + restore rules; RESET clears
S["rules"] = {}
cmds.file(saved, open=True)
check(w.sel() == ("MOR", "010", "MOR_010_0010", "7_fx") and S["rules"].get("scene") == base + "/1_projects", S["rules"])
check("Paths restored" in w.status_lbl.text(), w.status_lbl.text())
w.reset_paths()
check(S["rules"]["scene"] == "scenes" and not M._stored_paths(), "reset to defaults")

# copied scene in another shot → PATHS amber
w.set_paths(); cmds.file(rename=S["scene"]); cmds.file(save=True)
other = os.path.join(root, "VFX-MOR", "010", "MOR_010_0030", "3D", "7_fx", "1_projects", "copy.ma")
S["saved_fileinfo"][other] = dict(S["fileinfo"]); cmds.file(other, open=True); w._update_attention(force=True)
check(w.paths_btn.property("attention") and "another shot" in w.status_lbl.text(), "stale paths warned")
w.shot_cb.setCurrentText("MOR_010_0020"); w._update_attention(force=True)
check(w.get_btn.property("attention"), "GET amber on mismatch")
w.get_from_file(); w._update_attention(force=True)
check(not w.get_btn.property("attention"), "GET fixes it")

# SET RENDER: version from scene, frame naming, Arnold EXR, render layers
cmds.file(saved, open=True)
w.shotname_chk.setChecked(False)
w.set_render()
g = S["attrs"]
pub = base + "/3_publish/MOR_010_0010_fx_v001"
check(g["defaultRenderGlobals.imageFilePrefix"] == pub + "/MOR_010_0010_fx_v001", g)
check(g["defaultRenderGlobals.periodInExt"] == 2 and g["defaultRenderGlobals.extensionPadding"] == 4
      and g["defaultArnoldDriver.ai_translator"] == "exr", g)
S["layers"]["beauty"] = True; S["layers"]["shadow"] = True
w.set_render()
check(g["defaultRenderGlobals.imageFilePrefix"] == pub + "/<RenderLayer>/MOR_010_0010_fx_v001_<RenderLayer>"
      and "3 layers" in w.status_lbl.text(), g["defaultRenderGlobals.imageFilePrefix"])
del S["layers"]["beauty"], S["layers"]["shadow"]
os.makedirs(pub, exist_ok=True); open(pub + "/x.exr", "w").close()
QtWidgets.QMessageBox.exec = lambda self: [setattr(self, "_c", b) for b in self.buttons() if b.text().replace("&", "") == "New version"] and 0
QtWidgets.QMessageBox.clickedButton = lambda self: getattr(self, "_c", None)
w.set_render()
check(g["defaultRenderGlobals.imageFilePrefix"].endswith("MOR_010_0010_fx_v002/MOR_010_0010_fx_v002"), g["defaultRenderGlobals.imageFilePrefix"])
json.dump({"render_sep": "."}, open(P.CONFIG_PATH, "w")); w.shotname_chk.setChecked(True)
w.shot_cb.setCurrentText("MOR_010_0020"); w.task_cb.setCurrentText("7_fx")
QtWidgets.QMessageBox.exec = lambda self: 0
w.set_render()
check(g["defaultRenderGlobals.periodInExt"] == 1 and "MOR_010_0020_fx_v001" in g["defaultRenderGlobals.imageFilePrefix"], g)
check(P.load_state()["render_shot_name"] is True, "SHOT NAME shared state")
os.remove(P.CONFIG_PATH); w.shotname_chk.setChecked(False)

# + task, menus
w.shot_cb.setCurrentText("MOR_010_0010"); w._create_task("8_lighting")
check(w.task_cb.currentText() == "8_lighting", "task created")
w.task_cb.setCurrentText("7_fx"); w._fill_open_menu()
acts = [a.text() for a in w._open_menu.actions()]
check(any("_v002.ma" in a for a in acts) and not any(".hip" in a for a in acts), acts)
w._fill_save_menu(); check("_v003.ma" in w._save_menu.actions()[0].text(), "save menu next version")

# OPEN uses the OS dialog, starting in the task's scenes folder; cancel does nothing
seen = {}
QtWidgets.QFileDialog.getOpenFileName = staticmethod(lambda parent, cap, start, flt: (seen.setdefault("start", start), ("", ""))[1])
n_calls = len(S["calls"]); w.open_dialog()
check(seen["start"].endswith("/7_fx/1_projects") and len(S["calls"]) == n_calls, ("open dialog", seen))

# setup dialog is the shared one
dlg = Q.PipelineSetupDialog(w, host="Maya", version=M.VERSION)
check("MAYA" in dlg.windowTitle(), dlg.windowTitle())

w._set_status("Render set · EXR", Q.C_OK); w._update_attention(force=True); app.processEvents()
w.resize(w.sizeHint().width() + 20, w.sizeHint().height()); app.processEvents()
w.grab().save(os.path.join(OUT, "maya_bar.png"))
print(f"maya: {ok} checks passed")
