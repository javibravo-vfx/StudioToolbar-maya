# -*- coding: utf-8 -*-
"""
stm_qt — shared Qt look and Pipeline Setup dialog for Studio Toolbar (Houdini, and any Qt DCC)
Author: Javi Bravo (VFX)

Same palette, icons and Setup dialog as Studio Toolbar for MAX. The Setup dialog reads and
writes the same files as Max: ~/.studio-toolbar/pipeline_config.ini and pipeline_presets.json.

Sizes go through a scale function (set_scale) so hosts with their own UI scaling
(Houdini: hou.ui.scaledSize) stay crisp and proportional.
"""

import os, json

try:
    from PySide6 import QtWidgets, QtCore, QtGui, QtSvg
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui, QtSvg

import stm_pipeline as P

# ── scale ─────────────────────────────────────────────────────────────────────
_SCALE = {"fn": lambda px: px}

def set_scale(fn):
    _SCALE["fn"] = fn

def S(px):
    try:    return int(round(_SCALE["fn"](px)))
    except Exception: return px

# ── palette (Studio Toolbar for MAX) ──────────────────────────────────────────
MX_BG        = "#3c3c3c"
MX_BG_BTN_HO = "#505050"
MX_BG_BTN_PR = "#282828"
MX_BG_INPUT  = "#2e2e2e"
MX_BORDER    = "#555555"
MX_BORDER_HI = "#7a7a7a"
MX_TEXT      = "#d8d8d8"
MX_TEXT_DIM  = "#909090"
MX_SEP       = "#4a4a4a"
MX_SEL_BG    = "#4a6a8a"
IC_BASE      = "#b8b8b8"
IC_HOVER     = "#ffffff"

C_OK, C_ERR, C_WARN, C_DIM = "#70aa70", "#e06060", "#d4a017", "#909090"

# ── arrow SVGs on disk (stylesheets need files) — same files Max writes ───────
def ensure_style_icons():
    arrows = {
        "arrow_down":    '<path d="M3 5.5l4 4 4-4"/>',
        "arrow_up":      '<path d="M3 8.5l4-4 4 4"/>',
        "arrow_down_hi": '<path d="M3 5.5l4 4 4-4"/>',
    }
    try:
        os.makedirs(P.ICON_DIR, exist_ok=True)
        for name, body in arrows.items():
            col = "#ececec" if name.endswith("_hi") else "#b4b4b4"
            svg = (f'<svg viewBox="0 0 14 14" width="14" height="14" xmlns="http://www.w3.org/2000/svg" fill="none" '
                   f'stroke="{col}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
            path = os.path.join(P.ICON_DIR, name + ".svg")
            cur = open(path).read() if os.path.exists(path) else None
            if cur != svg:
                with open(path, "w") as f: f.write(svg)
    except Exception as e:
        print(f"[STM] style icons: {e}")

def icon_url(name):
    return os.path.join(P.ICON_DIR, name + ".svg").replace("\\", "/")

# ── mini icons (16×16) ────────────────────────────────────────────────────────
MINI_ICONS = {
    "save":   '<path d="M3 2.5h8l2.5 2.5v8.5h-10.5z"/><path d="M5.5 2.5v3.5h5v-3.5"/><rect x="5" y="9" width="6" height="4.5"/>',
    "trash":  '<path d="M2.5 4.5h11M6 4.5v-2h4v2M4 4.5l.7 9h6.6l.7-9M6.7 7v4.5M9.3 7v4.5"/>',
    "gear":   '<circle cx="8" cy="8" r="2"/><path d="M6.9 1.8h2.2l.4 1.8 1.2.7 1.8-.6 1.1 1.9-1.4 1.2v1.4l1.4 1.2-1.1 1.9-1.8-.6-1.2.7-.4 1.8H6.9l-.4-1.8-1.2-.7-1.8.6-1.1-1.9 1.4-1.2V7.3L1.4 6.1l1.1-1.9 1.8.6 1.2-.7z"/>',
    "folder": '<path d="M1.8 4.2v8.3h12.4V5.5H7.6L6.2 3.5H2.5z"/>',
    "plus":   '<path d="M8 3v10M3 8h10"/>',
    "refresh":'<path d="M13 8a5 5 0 1 1-1.5-3.6"/><path d="M13 2.5v3h-3"/>',
}

def _mi(body, c):
    return (f'<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="none" '
            f'stroke="{c}" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

def svg_pixmap(svg_str, size):
    r = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_str.encode()))
    pm = QtGui.QPixmap(size, size); pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm); r.render(p); p.end()
    return pm

def mini_icon(name, color=None, color_hover=None, size=16):
    icon = QtGui.QIcon()
    px = S(size) * 2
    for mode, col in ((QtGui.QIcon.Normal, color or IC_BASE),
                      (QtGui.QIcon.Active, color_hover or IC_HOVER),
                      (QtGui.QIcon.Disabled, "#5a5a5a")):
        pm = svg_pixmap(_mi(MINI_ICONS[name], col), px)
        pm.setDevicePixelRatio(2.0)
        icon.addPixmap(pm, mode, QtGui.QIcon.Off)
    return icon

def H():
    return S(22)

def mini_btn(icon, tooltip, obj="mini_btn"):
    b = QtWidgets.QToolButton()
    b.setObjectName(obj)
    b.setIcon(icon if isinstance(icon, QtGui.QIcon) else mini_icon(icon))
    b.setIconSize(QtCore.QSize(S(16), S(16)))
    b.setFixedSize(S(24), H())
    b.setToolTip(tooltip)
    b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    return b

def action_btn(text, tip):
    b = QtWidgets.QPushButton(text)
    b.setObjectName("action_btn"); b.setFixedHeight(H()); b.setToolTip(tip)
    b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    return b

def split_btn(text, tip):
    b = QtWidgets.QToolButton()
    b.setObjectName("action_btn"); b.setText(text); b.setFixedHeight(H()); b.setToolTip(tip)
    b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    b.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
    b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    m = QtWidgets.QMenu(b); b.setMenu(m)
    return b, m

def section_label(text):
    l = QtWidgets.QLabel(text); l.setObjectName("section_lbl"); return l

def section_sep(layout):
    layout.addSpacing(S(10))
    line = QtWidgets.QFrame(); line.setObjectName("sep"); line.setFrameShape(QtWidgets.QFrame.VLine)
    line.setFixedWidth(1); line.setFixedHeight(H())
    layout.addWidget(line)
    layout.addSpacing(S(10))

def combo(width, tip):
    c = QtWidgets.QComboBox()
    c.setFixedWidth(S(width)); c.setFixedHeight(H()); c.setToolTip(tip)
    c.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    c.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
    c.view().setMinimumWidth(S(width))
    return c

def menu_header(m, text):
    a = m.addAction(text.upper()); a.setEnabled(False)
    f = a.font(); f.setBold(True); f.setPointSizeF(max(6.5, f.pointSizeF() * 0.85)); a.setFont(f)
    return a

# ── toolbar stylesheet (Max look; fonts inherited from the host) ──────────────
def toolbar_style():
    ensure_style_icons()
    h = H()
    return f"""
QWidget#stm_root, QWidget#stm_root QWidget {{ background-color: {MX_BG}; color: {MX_TEXT}; }}
QWidget#stm_root QLabel {{ background: transparent; color: {MX_TEXT_DIM}; }}
QLabel#section_lbl {{ color: {MX_TEXT_DIM}; font-weight: bold; }}
QFrame#sep {{ background: {MX_SEP}; border: none; }}

QComboBox {{
    background-color: {MX_BG_INPUT}; color: {MX_TEXT};
    border: 1px solid {MX_BORDER}; border-radius: 1px;
    padding: 0px {S(18)}px 0px {S(6)}px; min-height: {h - 2}px; max-height: {h}px;
    selection-background-color: {MX_SEL_BG};
}}
QComboBox:hover, QComboBox:focus {{ border-color: {MX_BORDER_HI}; }}
QComboBox:disabled {{ color: #6a6a6a; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
                        border: none; width: {S(16)}px; background: transparent; }}
QComboBox::down-arrow {{ image: url({icon_url("arrow_down")}); width: {S(10)}px; height: {S(10)}px; }}
QComboBox::down-arrow:hover, QComboBox::down-arrow:on {{ image: url({icon_url("arrow_down_hi")}); }}
QComboBox QAbstractItemView {{
    background-color: #2a2a2a; color: {MX_TEXT}; border: 1px solid {MX_BORDER};
    selection-background-color: {MX_SEL_BG}; outline: none;
}}

QPushButton#action_btn, QToolButton#action_btn {{
    background-color: #484848; color: {MX_TEXT};
    border: 1px solid {MX_BORDER}; border-radius: 1px;
    padding: 0px {S(10)}px; min-height: {h - 2}px;
}}
QToolButton#action_btn {{ padding-right: {S(20)}px; }}
QPushButton#action_btn:hover, QToolButton#action_btn:hover {{ background-color: {MX_BG_BTN_HO}; border-color: {MX_BORDER_HI}; }}
QPushButton#action_btn:pressed, QToolButton#action_btn:pressed {{ background-color: {MX_BG_BTN_PR}; }}
QToolButton#action_btn::menu-button {{
    width: {S(15)}px; border: none; border-left: 1px solid {MX_BORDER}; background: transparent;
}}
QToolButton#action_btn::menu-button:hover {{ background-color: #5c5c5c; }}
QToolButton#action_btn::menu-arrow {{ image: url({icon_url("arrow_down")}); width: {S(9)}px; height: {S(9)}px; }}
QPushButton#action_btn[attention="true"] {{ color: #f0c060; border-color: #a07a2a; background-color: #4a4232; }}

QPushButton#reset_btn {{
    background-color: #3a2e2e; color: #c08080; border: 1px solid #5a4040; border-radius: 1px;
    padding: 0px {S(10)}px; min-height: {h - 2}px;
}}
QPushButton#reset_btn:hover {{ background-color: #583030; color: #e06060; border-color: #884444; }}
QPushButton#reset_btn:pressed {{ background-color: #1e1010; }}

QToolButton#mini_btn, QToolButton#mini_del {{
    background-color: #464646; border: 1px solid {MX_BORDER}; border-radius: 2px; padding: 0;
}}
QToolButton#mini_btn:hover {{ background-color: {MX_BG_BTN_HO}; border-color: {MX_BORDER_HI}; }}
QToolButton#mini_btn:pressed {{ background-color: {MX_BG_BTN_PR}; }}
QToolButton#mini_del:hover {{ background-color: #583030; border-color: #884444; }}
QToolButton#mini_btn::menu-indicator {{ image: none; width: 0; }}

QCheckBox {{ color: {MX_TEXT}; spacing: {S(5)}px; background: transparent; }}
QCheckBox::indicator {{
    width: {S(13)}px; height: {S(13)}px;
    background-color: {MX_BG_INPUT}; border: 1px solid {MX_BORDER}; border-radius: 1px;
}}
QCheckBox::indicator:checked {{ background-color: #5a8aaa; border-color: {MX_BORDER_HI}; }}

QLabel#status_lbl {{ color: {MX_TEXT_DIM}; padding: 0 {S(2)}px; }}
QLabel#status_lbl:hover {{ color: {MX_TEXT}; }}

QMenu {{
    background-color: #323232; color: {MX_TEXT}; border: 1px solid {MX_BORDER}; padding: {S(2)}px 0;
}}
QMenu::item {{ padding: {S(5)}px {S(22)}px {S(5)}px {S(10)}px; background: transparent; }}
QMenu::item:selected {{ background-color: {MX_SEL_BG}; color: #ffffff; }}
QMenu::item:disabled {{ color: #6a6a6a; }}
QMenu::separator {{ height: 1px; background: {MX_SEP}; margin: {S(2)}px {S(6)}px; }}
QToolTip {{ background-color: #2a2a2a; color: {MX_TEXT}; border: 1px solid {MX_BORDER}; padding: {S(3)}px {S(7)}px; }}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  Pipeline Setup — ported from Studio Toolbar for MAX (same files, same keys)
# ══════════════════════════════════════════════════════════════════════════════
def _dialog_style():
    ensure_style_icons()
    return f"""
    QDialog {{ background-color: #2b2b2b; color: {MX_TEXT}; }}
    QWidget#page, QWidget#footer {{ background: transparent; }}
    QLabel {{ color: #9a9a9a; background: transparent; }}
    QLabel#page_title {{ color: #e6e6e6; font-size: {S(17)}px; font-weight: 600; }}
    QLabel#page_sub   {{ color: #8a8a8a; }}
    QLabel#field_lbl  {{ color: #b0b0b0; }}
    QLabel#hint       {{ color: #6f6f6f; }}
    QLabel#card_title {{ color: #c8c8c8; font-weight: 600; }}
    QLabel#tree {{
        background: #1f1f1f; border: 1px solid #3c3c3c; border-radius: {S(4)}px;
        color: #b8b8b8; font-family: "Consolas", "Cascadia Mono", "DejaVu Sans Mono", monospace;
        padding: {S(10)}px {S(12)}px;
    }}
    QLabel#preview {{ color: #7fb6c9; font-family: "Consolas", "DejaVu Sans Mono", monospace; }}
    QFrame#card {{ background: #313131; border: 1px solid #3d3d3d; border-radius: {S(5)}px; }}

    QListWidget#nav {{
        background: #242424; border: none; border-right: 1px solid #3a3a3a; outline: none; padding-top: {S(10)}px;
    }}
    QListWidget#nav::item {{ color: #a8a8a8; padding: {S(9)}px {S(16)}px; border-left: 3px solid transparent; }}
    QListWidget#nav::item:hover {{ background: #2e2e2e; color: #dddddd; }}
    QListWidget#nav::item:selected {{ background: #333a3e; color: #ffffff; border-left: 3px solid #4ec9c9; }}

    QLineEdit, QListWidget, QComboBox {{
        background-color: #1f1f1f; color: {MX_TEXT}; border: 1px solid #4a4a4a; border-radius: {S(3)}px;
        padding: {S(4)}px {S(7)}px; selection-background-color: #3f6f80;
    }}
    QComboBox {{ padding-right: {S(22)}px; }}
    QListWidget {{ padding: {S(3)}px; }}
    QListWidget::item {{ padding: {S(4)}px {S(6)}px; border-radius: 2px; color: {MX_TEXT}; }}
    QListWidget::item:selected {{ background: #3a5560; color: #ffffff; }}
    QListWidget::item:hover {{ background: #2a2a2a; }}
    QLineEdit:focus, QListWidget:focus, QComboBox:focus {{ border-color: #4ec9c9; }}
    QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; border: none; width: {S(20)}px; }}
    QComboBox::down-arrow {{ image: url({icon_url("arrow_down")}); width: {S(11)}px; height: {S(11)}px; }}
    QComboBox QAbstractItemView {{ background-color: #1f1f1f; color: {MX_TEXT}; border: 1px solid #4a4a4a;
                                   selection-background-color: #3a5560; outline: none; }}
    QCheckBox {{ color: #c8c8c8; spacing: {S(6)}px; background: transparent; }}
    QCheckBox::indicator {{ width: {S(14)}px; height: {S(14)}px; background: #1f1f1f; border: 1px solid #555; border-radius: 3px; }}
    QCheckBox::indicator:checked {{ background: #3f8a9a; border-color: #4ec9c9; }}

    QPushButton {{
        background-color: #3a3a3a; color: {MX_TEXT}; border: 1px solid #505050; border-radius: {S(3)}px;
        padding: {S(5)}px {S(14)}px;
    }}
    QPushButton:hover {{ background-color: #474747; border-color: #6a6a6a; }}
    QPushButton:pressed {{ background-color: #252525; }}
    QPushButton#ok_btn {{ background-color: #2f5560; color: #ffffff; border-color: #4ec9c9; font-weight: 600;
                          padding: {S(6)}px {S(20)}px; }}
    QPushButton#ok_btn:hover {{ background-color: #386673; }}
    QPushButton#flat_btn {{ background: transparent; border-color: transparent; color: #a8a8a8; }}
    QPushButton#flat_btn:hover {{ background: #3a3a3a; border-color: #505050; color: #e0e0e0; }}
    QToolButton#mini_btn, QToolButton#mini_del {{
        background-color: #3a3a3a; border: 1px solid #505050; border-radius: {S(3)}px; padding: 0;
    }}
    QToolButton#mini_btn:hover {{ background-color: #484848; border-color: #6a6a6a; }}
    QToolButton#mini_del:hover {{ background-color: #583030; border-color: #884444; }}
    QWidget#footer {{ border-top: 1px solid #3a3a3a; }}
    QToolTip {{ background-color: #2a2a2a; color: {MX_TEXT}; border: 1px solid {MX_BORDER}; }}
    """


class PipelineSetupDialog(QtWidgets.QDialog):
    """Pipeline setup — writes ~/.studio-toolbar/pipeline_config.ini (shared with Max)
    and named presets to ~/.studio-toolbar/pipeline_presets.json."""

    def __init__(self, parent=None, host="Houdini", version="", scene_label="Scene filename"):
        super().__init__(parent)
        self.setWindowTitle(f"Pipeline Setup  —  Studio Toolbar for {host.upper()}" + (f"  v{version}" if version else ""))
        self.setStyleSheet(_dialog_style())
        self._scene_label = scene_label
        self.cfg = P.cfg_raw()
        self._build()
        for child in self.findChildren(QtWidgets.QLineEdit):
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Enter in a field just leaves the field (never closes the dialog)."""
        if isinstance(obj, QtWidgets.QLineEdit) and event.type() == QtCore.QEvent.KeyPress \
                and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            obj.clearFocus()
            return True
        return super().eventFilter(obj, event)

    # ── psub mapping (subfolders inside each task's scenes folder) ────────────
    def _on_psub_task_changed(self, task_name):
        if getattr(self, "_psub_last_task", None):
            self._psub_mapping[self._psub_last_task] = self._list_items(self.psub_list)
        self._psub_last_task = task_name
        self.psub_list.clear()
        if task_name not in self._psub_mapping:
            self._psub_mapping[task_name] = ["textures"]
        for s in self._psub_mapping[task_name]:
            self.psub_list.addItem(s)

    def _sync_psub_task_combo(self):
        current = self.psub_task_cb.currentText()
        tasks = self._list_items(self.task_list)
        self.psub_task_cb.blockSignals(True)
        self.psub_task_cb.clear()
        for t in tasks: self.psub_task_cb.addItem(t)
        if current in tasks: self.psub_task_cb.setCurrentText(current)
        self.psub_task_cb.blockSignals(False)

    def _current_form_data(self):
        if getattr(self, "_psub_last_task", None):
            self._psub_mapping[self._psub_last_task] = self._list_items(self.psub_list)
        tasks = self._list_items(self.task_list)
        subs  = self._list_items(self.sub_list)
        return {
            "root_drive":         self.ed_drive.text().strip().rstrip("\\"),
            "project_prefix":     self.ed_prefix.text().strip(),
            "seq_exclude":        self.ed_exclude.text().strip(),
            "tasks":              ",".join(tasks),
            "sub_projects":       subs[0] if len(subs) > 0 else "1_projects",
            "sub_review":         subs[1] if len(subs) > 1 else "2_review",
            "sub_publish":        subs[2] if len(subs) > 2 else "3_publish",
            "extra_subs":         ",".join(subs[3:]) if len(subs) > 3 else "",
            "task_projects_subs": json.dumps(self._psub_mapping) if self._psub_mapping else "",
            "thumb_subfolder":    self.thumb_sub_cb.currentText(),
            "thumb_subdir":       self.ed_thumb_subdir.text().strip(),
            "snap_inc_maxfile":   self.chk_snap_maxfile.isChecked(),
            "snap_inc_shot":      self.chk_snap_shot.isChecked(),
            "snap_inc_task":      self.chk_snap_task.isChecked(),
            "snap_inc_camera":    self.chk_snap_camera.isChecked(),
            "render_sep":         "_" if self.render_sep_cb.currentIndex() == 0 else ".",
        }

    @staticmethod
    def _bool(cfg, key, default):
        v = cfg.get(key, default)
        return v if isinstance(v, bool) else (str(v).lower() != "false" if default else str(v).lower() == "true")

    def _apply_cfg_to_form(self, cfg):
        self.ed_drive.setText(cfg.get("root_drive", "T:"))
        self.ed_prefix.setText(cfg.get("project_prefix", "VFX-"))
        self.ed_exclude.setText(cfg.get("seq_exclude", "3D,SOURCE,FOOTAGE"))
        self.task_list.clear()
        for t in [t.strip() for t in cfg.get("tasks", "").split(",") if t.strip()]:
            self.task_list.addItem(t)
        self._sync_psub_task_combo()
        self.sub_list.clear()
        for s in self._subs_of(cfg): self.sub_list.addItem(s)
        self._psub_mapping = self._mapping_of(cfg)
        self._psub_last_task = None
        if self.psub_task_cb.count() > 0:
            self._on_psub_task_changed(self.psub_task_cb.currentText())
        self._refresh_thumb_sub_combo()
        thumb = cfg.get("thumb_subfolder", "")
        if thumb and self.thumb_sub_cb.findText(thumb) >= 0:
            self.thumb_sub_cb.setCurrentText(thumb)
        self.ed_thumb_subdir.setText(cfg.get("thumb_subdir", ""))
        self.chk_snap_maxfile.setChecked(self._bool(cfg, "snap_inc_maxfile", True))
        self.chk_snap_shot.setChecked(self._bool(cfg, "snap_inc_shot", False))
        self.chk_snap_task.setChecked(self._bool(cfg, "snap_inc_task", False))
        self.chk_snap_camera.setChecked(self._bool(cfg, "snap_inc_camera", True))
        self.render_sep_cb.setCurrentIndex(0 if cfg.get("render_sep", "_") == "_" else 1)
        self._update_snap_preview()
        self._update_previews()

    @staticmethod
    def _subs_of(cfg):
        subs = [cfg.get(k, "").strip() for k in ("sub_projects", "sub_review", "sub_publish")]
        subs = [s for s in subs if s]
        return subs + [v.strip() for v in cfg.get("extra_subs", "").split(",") if v.strip()]

    @staticmethod
    def _mapping_of(cfg):
        raw = cfg.get("task_projects_subs", "")
        try:    return (json.loads(raw) if isinstance(raw, str) else dict(raw)) if raw else {}
        except Exception: return {}

    # ── layout helpers ────────────────────────────────────────────────────────
    def _page(self, title, subtitle):
        w = QtWidgets.QWidget(); w.setObjectName("page")
        v = QtWidgets.QVBoxLayout(w); v.setContentsMargins(S(26), S(22), S(26), S(18)); v.setSpacing(S(12))
        t = QtWidgets.QLabel(title); t.setObjectName("page_title")
        st = QtWidgets.QLabel(subtitle); st.setObjectName("page_sub"); st.setWordWrap(True)
        v.addWidget(t); v.addWidget(st); v.addSpacing(S(6))
        return w, v

    @staticmethod
    def _card(title=None):
        f = QtWidgets.QFrame(); f.setObjectName("card")
        v = QtWidgets.QVBoxLayout(f); v.setContentsMargins(S(14), S(12), S(14), S(12)); v.setSpacing(S(8))
        if title:
            t = QtWidgets.QLabel(title); t.setObjectName("card_title"); v.addWidget(t)
        return f, v

    @staticmethod
    def _field(text):
        l = QtWidgets.QLabel(text); l.setObjectName("field_lbl"); return l

    @staticmethod
    def _hint(text):
        l = QtWidgets.QLabel(text); l.setObjectName("hint"); l.setWordWrap(True); return l

    def _list_editor(self, listw, line_edit, placeholder, label):
        box = QtWidgets.QVBoxLayout(); box.setSpacing(S(6))
        listw.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        listw.itemDoubleClicked.connect(self._rename_item)
        box.addWidget(listw, 1)
        row = QtWidgets.QHBoxLayout(); row.setSpacing(S(4))
        line_edit.setPlaceholderText(placeholder); line_edit.setMinimumWidth(S(130))
        add = mini_btn("plus", f"Add {label}"); add.setFixedSize(S(30), S(28))
        dele = mini_btn("trash", f"Delete selected {label}", obj="mini_del"); dele.setFixedSize(S(30), S(28))
        add.clicked.connect(lambda: self._add_item(listw, line_edit))
        line_edit.returnPressed.connect(lambda: self._add_item(listw, line_edit))
        dele.clicked.connect(lambda: self._del_item(listw, label))
        row.addWidget(line_edit, 1); row.addWidget(add); row.addWidget(dele)
        box.addLayout(row)
        return box

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        outer = QtWidgets.QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        body = QtWidgets.QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        outer.addLayout(body, 1)
        self.nav = QtWidgets.QListWidget(); self.nav.setObjectName("nav"); self.nav.setFixedWidth(S(170))
        self.pages = QtWidgets.QStackedWidget()
        body.addWidget(self.nav); body.addWidget(self.pages, 1)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)

        subs  = self._subs_of(self.cfg)
        tasks = [t.strip() for t in self.cfg.get("tasks", "").split(",") if t.strip()]

        # PROJECT
        pg, v = self._page("Project", "Where your projects live and how the toolbar recognises them. "
                                      "Shared with Studio Toolbar for MAX.")
        card, c = self._card()
        form = QtWidgets.QGridLayout(); form.setHorizontalSpacing(S(12)); form.setVerticalSpacing(S(10))
        self.ed_drive = QtWidgets.QLineEdit(self.cfg.get("root_drive", "T:"))
        self.ed_drive.setToolTip("Root drive or path where projects live  (e.g.  T:  or  //server/projects)")
        browse = QtWidgets.QPushButton("Browse…"); browse.setObjectName("flat_btn")
        browse.clicked.connect(self._browse_root)
        self.ed_prefix = QtWidgets.QLineEdit(self.cfg.get("project_prefix", "VFX-"))
        self.ed_prefix.setToolTip("Prefix that identifies project folders  (e.g.  VFX-  → folders named  VFX-MOR…)")
        self.ed_prefix.setMaximumWidth(S(160))
        self.ed_exclude = QtWidgets.QLineEdit(self.cfg.get("seq_exclude", "3D,SOURCE,FOOTAGE"))
        self.ed_exclude.setToolTip("e.g.  3D,SOURCE,FOOTAGE,AUDIO,RENDER")
        form.addWidget(self._field("Root path"), 0, 0); form.addWidget(self.ed_drive, 0, 1); form.addWidget(browse, 0, 2)
        form.addWidget(self._field("Project prefix"), 1, 0); form.addWidget(self.ed_prefix, 1, 1, 1, 2, QtCore.Qt.AlignLeft)
        form.addWidget(self._field("Not sequences"), 2, 0); form.addWidget(self.ed_exclude, 2, 1, 1, 2)
        form.addWidget(self._hint("Folders inside a project that should not be listed as sequences — "
                                  "comma-separated, case-insensitive."), 3, 1, 1, 2)
        form.setColumnStretch(1, 1)
        c.addLayout(form); v.addWidget(card)
        self._proj_preview = QtWidgets.QLabel(); self._proj_preview.setObjectName("preview")
        self._proj_found = QtWidgets.QLabel(); self._proj_found.setWordWrap(True)
        v.addWidget(self._hint("Project folders look like:")); v.addWidget(self._proj_preview)
        v.addSpacing(S(4)); v.addWidget(self._proj_found)
        if os.environ.get("STM_ROOT"):
            v.addWidget(self._hint(f"This machine overrides the root with STM_ROOT = {os.environ['STM_ROOT']}"))
        v.addStretch()
        self._add_page("Project", pg)

        # TASKS
        pg, v = self._page("Tasks", "Department folders created with the  +  button. Select a task to choose "
                                    "the subfolders created inside its scenes folder.")
        row = QtWidgets.QHBoxLayout(); row.setSpacing(S(14))
        card, c = self._card("Task folders")
        self.task_list = QtWidgets.QListWidget()
        for t in tasks: self.task_list.addItem(t)
        self.ed_new_task = QtWidgets.QLineEdit()
        c.addLayout(self._list_editor(self.task_list, self.ed_new_task, "new task…", "task"), 1)
        c.addWidget(self._hint("Drag to reorder · double-click to rename"))
        row.addWidget(card, 1)
        card, c = self._card()
        self._psub_title = QtWidgets.QLabel(); self._psub_title.setObjectName("card_title")
        c.addWidget(self._psub_title)
        self.psub_task_cb = QtWidgets.QComboBox(); self.psub_task_cb.setVisible(False)
        for t in tasks: self.psub_task_cb.addItem(t)
        self.psub_list = QtWidgets.QListWidget()
        self.psub_list.setToolTip("Subfolders to create inside this task's scenes folder")
        self.ed_new_psub = QtWidgets.QLineEdit()
        c.addLayout(self._list_editor(self.psub_list, self.ed_new_psub, "new subfolder…", "subfolder"), 1)
        c.addWidget(self._hint("Tasks you never touch get  textures/  by default."))
        row.addWidget(card, 1)
        v.addLayout(row, 1)
        self._add_page("Tasks", pg)
        self.task_list.model().rowsInserted.connect(self._sync_psub_task_combo)
        self.task_list.model().rowsRemoved.connect(self._sync_psub_task_combo)
        self.task_list.currentTextChanged.connect(self._on_task_selected)
        self._psub_mapping = self._mapping_of(self.cfg)
        self.psub_task_cb.currentTextChanged.connect(self._on_psub_task_changed)
        if self.psub_task_cb.count() > 0:
            self._on_psub_task_changed(self.psub_task_cb.currentText())

        # FOLDERS
        pg, v = self._page("Folders", "Subfolders created inside every task. The first three have fixed roles; "
                                      "extras are optional.")
        row = QtWidgets.QHBoxLayout(); row.setSpacing(S(14))
        card, c = self._card("Task subfolders")
        self.sub_list = QtWidgets.QListWidget()
        for s_ in subs: self.sub_list.addItem(s_)
        self.ed_new_sub = QtWidgets.QLineEdit()
        c.addLayout(self._list_editor(self.sub_list, self.ed_new_sub, "new subfolder…", "subfolder"), 1)
        c.addWidget(self._hint("1st = scenes · 2nd = review · 3rd = publish (renders)"))
        card.setMinimumWidth(S(240))
        row.addWidget(card, 1)
        card, c = self._card("Resulting structure")
        self._tree_lbl = QtWidgets.QLabel(); self._tree_lbl.setObjectName("tree")
        self._tree_lbl.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self._tree_lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        c.addWidget(self._tree_lbl, 1)
        row.addWidget(card, 1)
        v.addLayout(row, 1)
        self._add_page("Folders", pg)
        self.sub_list.model().rowsInserted.connect(self._refresh_thumb_sub_combo)
        self.sub_list.model().rowsRemoved.connect(self._refresh_thumb_sub_combo)

        # OUTPUT
        pg, v = self._page("Output", "Where viewport snapshots go, how they are named, and how render frames are numbered.")
        card, c = self._card("Viewport snapshots")
        grid = QtWidgets.QGridLayout(); grid.setHorizontalSpacing(S(12)); grid.setVerticalSpacing(S(10))
        self.thumb_sub_cb = QtWidgets.QComboBox(); self.thumb_sub_cb.setMinimumWidth(S(180))
        self.thumb_sub_cb.setToolTip("Which task subfolder receives the snapshots")
        for s_ in subs: self.thumb_sub_cb.addItem(s_)
        saved_thumb = self.cfg.get("thumb_subfolder", subs[1] if len(subs) > 1 else "")
        if saved_thumb and self.thumb_sub_cb.findText(saved_thumb) >= 0:
            self.thumb_sub_cb.setCurrentText(saved_thumb)
        self.ed_thumb_subdir = QtWidgets.QLineEdit(self.cfg.get("thumb_subdir", ""))
        self.ed_thumb_subdir.setPlaceholderText("optional — e.g.  captures")
        self.ed_thumb_subdir.setToolTip("If set, snapshots go into  task / subfolder / <this>  —  created automatically")
        grid.addWidget(self._field("Save into"), 0, 0); grid.addWidget(self.thumb_sub_cb, 0, 1, QtCore.Qt.AlignLeft)
        grid.addWidget(self._field("Inside folder"), 1, 0); grid.addWidget(self.ed_thumb_subdir, 1, 1)
        chk_row = QtWidgets.QHBoxLayout(); chk_row.setSpacing(S(16))
        self.chk_snap_maxfile = QtWidgets.QCheckBox(self._scene_label)
        self.chk_snap_shot    = QtWidgets.QCheckBox("Shot")
        self.chk_snap_task    = QtWidgets.QCheckBox("Task")
        self.chk_snap_camera  = QtWidgets.QCheckBox("Camera / view")
        self.chk_snap_maxfile.setChecked(self._bool(self.cfg, "snap_inc_maxfile", True))
        self.chk_snap_shot.setChecked(self._bool(self.cfg, "snap_inc_shot", False))
        self.chk_snap_task.setChecked(self._bool(self.cfg, "snap_inc_task", False))
        self.chk_snap_camera.setChecked(self._bool(self.cfg, "snap_inc_camera", True))
        for chk in (self.chk_snap_maxfile, self.chk_snap_shot, self.chk_snap_task, self.chk_snap_camera):
            chk_row.addWidget(chk); chk.toggled.connect(self._update_snap_preview)
        chk_row.addStretch()
        grid.addWidget(self._field("Name parts"), 2, 0); grid.addLayout(chk_row, 2, 1)
        self._snap_preview_lbl = QtWidgets.QLabel(); self._snap_preview_lbl.setObjectName("preview")
        grid.addWidget(self._field("Example"), 3, 0); grid.addWidget(self._snap_preview_lbl, 3, 1)
        grid.setColumnStretch(1, 1)
        c.addLayout(grid); v.addWidget(card)
        card, c = self._card("Render frames")
        rr = QtWidgets.QHBoxLayout(); rr.setSpacing(S(12))
        self.render_sep_cb = QtWidgets.QComboBox()
        self.render_sep_cb.addItems(["Underscore   shot_v001_0001.exr", "Dot   shot_v001.0001.exr"])
        self.render_sep_cb.setCurrentIndex(0 if self.cfg.get("render_sep", "_") == "_" else 1)
        rr.addWidget(self._field("Frame separator")); rr.addWidget(self.render_sep_cb); rr.addStretch()
        c.addLayout(rr); v.addWidget(card)
        v.addStretch()
        self._add_page("Output", pg)
        self._update_snap_preview()

        # FOOTER
        footer = QtWidgets.QWidget(); footer.setObjectName("footer")
        fl = QtWidgets.QHBoxLayout(footer); fl.setContentsMargins(S(16), S(12), S(16), S(12)); fl.setSpacing(S(6))
        fl.addWidget(self._field("Preset"))
        self.preset_cb = QtWidgets.QComboBox(); self.preset_cb.setMinimumWidth(S(180))
        self.preset_cb.setToolTip("Saved pipeline configurations (shared with Max)")
        self._refresh_preset_combo()
        btn_load = QtWidgets.QPushButton("Load"); btn_load.setObjectName("flat_btn")
        btn_load.setToolTip("Load the selected preset into this dialog (applied when you press Save & Apply)")
        btn_save = QtWidgets.QPushButton("Save as…"); btn_save.setObjectName("flat_btn")
        btn_save.setToolTip("Save the current settings as a named preset")
        btn_del = mini_btn("trash", "Delete the selected preset", obj="mini_del"); btn_del.setFixedSize(S(28), S(26))
        btn_load.clicked.connect(self._load_preset)
        btn_save.clicked.connect(self._save_preset_as)
        btn_del.clicked.connect(self._delete_preset)
        for w in (self.preset_cb, btn_load, btn_save, btn_del): fl.addWidget(w)
        fl.addStretch()
        cfg_link = QtWidgets.QPushButton("Config folder"); cfg_link.setObjectName("flat_btn")
        cfg_link.setToolTip(f"{P.CONFIG_PATH}\n{P.PRESETS_PATH}")
        cfg_link.clicked.connect(lambda: P.open_folder(P.PIPE_DIR))
        fl.addWidget(cfg_link); fl.addSpacing(S(10))
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_ok = QtWidgets.QPushButton("Save && Apply"); btn_ok.setObjectName("ok_btn")
        for btn in (btn_cancel, btn_ok, btn_load, btn_save, cfg_link):
            btn.setAutoDefault(False); btn.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._save_and_accept)
        fl.addWidget(btn_cancel); fl.addWidget(btn_ok)
        outer.addWidget(footer)

        for ed in (self.ed_drive, self.ed_prefix):
            ed.textChanged.connect(self._update_previews)
        for lw in (self.sub_list, self.psub_list, self.task_list):
            m = lw.model()
            for sig in (m.rowsInserted, m.rowsRemoved, m.rowsMoved, m.dataChanged):
                sig.connect(self._update_previews)
        self.ed_thumb_subdir.textChanged.connect(self._update_previews)
        self.thumb_sub_cb.currentTextChanged.connect(self._update_previews)

        if self.task_list.count(): self.task_list.setCurrentRow(len(tasks) - 1)
        self.nav.setCurrentRow(0)
        self._do_update_previews()

        # Never squash text: buttons/labels keep at least their text width
        for w in [x for cls in (QtWidgets.QPushButton, QtWidgets.QLabel, QtWidgets.QCheckBox)
                  for x in self.findChildren(cls)]:
            if isinstance(w, QtWidgets.QLabel) and (w.wordWrap() or w.objectName() in ("tree", "preview")):
                continue
            w.ensurePolished(); w.setMinimumWidth(w.sizeHint().width())
        self.preset_cb.setMaximumWidth(S(260))
        outer.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.resize(max(S(860), self.minimumSizeHint().width()), max(S(600), self.minimumSizeHint().height()))

    def _add_page(self, name, widget):
        self.nav.addItem(name); self.pages.addWidget(widget)

    def _browse_root(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Projects root", self.ed_drive.text() or "")
        if d: self.ed_drive.setText(os.path.normpath(d))

    def _on_task_selected(self, task):
        if task and self.psub_task_cb.findText(task) >= 0:
            self.psub_task_cb.setCurrentText(task)
        self._update_previews()

    @staticmethod
    def _list_items(listw):
        return [listw.item(i).text().strip() for i in range(listw.count()) if listw.item(i).text().strip()]

    def _update_previews(self, *a):
        """Debounced: list edits, typing and drags fire many signals in a row;
        the previews are rebuilt once, 120 ms after the last one."""
        if not hasattr(self, "_tree_lbl"): return
        if not hasattr(self, "_prev_timer"):
            self._prev_timer = QtCore.QTimer(self)
            self._prev_timer.setSingleShot(True)
            self._prev_timer.timeout.connect(self._do_update_previews)
        self._prev_timer.start(120)

    def _scan_projects(self, scan_root, prefix):
        """Projects under the root — scanned once per (root, prefix), not on every edit
        (on a network drive each scan can take a while)."""
        cache = self.__dict__.setdefault("_scan_cache", {})
        key = (scan_root, prefix)
        if key not in cache:
            cache[key] = None if not os.path.isdir(scan_root) else \
                sorted(d[len(prefix):] for d in P.listdirs(scan_root) if d.startswith(prefix))
        return cache[key]

    def _do_update_previews(self):
        if not hasattr(self, "_tree_lbl"): return
        prefix = self.ed_prefix.text().strip() or "VFX-"
        root   = self.ed_drive.text().strip().rstrip("\\/") or "T:"
        sep    = "\\" if (":" in root or root.startswith("\\\\")) else "/"
        self._proj_preview.setText(f"{root}{sep}{prefix}MYPROJECT{sep}")
        scan_root = root + os.sep if root.endswith(":") else root
        found = self._scan_projects(scan_root, prefix)
        if found is None:
            self._proj_found.setText("⚠  Root path not found on this machine")
            self._proj_found.setStyleSheet("color: #e07a6a;")
        else:
            if found:
                more = f"  +{len(found) - 10} more" if len(found) > 10 else ""
                self._proj_found.setText(f"✓  {len(found)} project{'s' if len(found) != 1 else ''} found:  "
                                         + ",  ".join(found[:10]) + more)
                self._proj_found.setStyleSheet("color: #78b878;")
            else:
                self._proj_found.setText(f"No folders starting with  “{prefix}”  in this root")
                self._proj_found.setStyleSheet("color: #d4a017;")
        subs  = self._list_items(self.sub_list) or ["1_projects"]
        task  = self.task_list.currentItem().text() if self.task_list.currentItem() else \
                (self._list_items(self.task_list) or ["task"])[0]
        psubs = self._list_items(self.psub_list) if self.psub_task_cb.currentText() == task else \
                self._psub_mapping.get(task, ["textures"])
        roles = {0: "scenes", 1: "review", 2: "renders"}
        snap_sub = self.thumb_sub_cb.currentText()
        lines = [f"{root}{sep}{prefix}PROJ{sep}", f"  101{sep}  PROJ_101_010{sep}  3D{sep}", f"    {task}{sep}"]
        for i, sb in enumerate(subs):
            tag = roles.get(i, "")
            if sb == snap_sub: tag = (tag + " · snapshots").strip(" ·")
            lines.append(f"      {sb}{sep}".ljust(30) + (f"← {tag}" if tag else ""))
            if i == 0:
                for ps in psubs: lines.append(f"        {ps}{sep}")
            if sb == snap_sub and self.ed_thumb_subdir.text().strip():
                lines.append(f"        {self.ed_thumb_subdir.text().strip()}{sep}")
        self._tree_lbl.setText("\n".join(lines))
        if task:
            self._psub_title.setText(f"Inside  {task} › {subs[0]}")

    # list helpers
    def _add_item(self, listw, line_edit):
        txt = line_edit.text().strip()
        if txt: listw.addItem(txt); line_edit.clear()

    def _del_item(self, listw, label):
        row = listw.currentRow()
        if row < 0: return
        item = listw.item(row)
        if QtWidgets.QMessageBox.question(self, f"Delete {label}", f"Remove  '{item.text()}'?",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel) == QtWidgets.QMessageBox.Ok:
            listw.takeItem(row)

    def _rename_item(self, item):
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename", "New name:", text=item.text())
        if ok and new_name.strip(): item.setText(new_name.strip())

    # presets
    def _refresh_thumb_sub_combo(self):
        if not hasattr(self, "thumb_sub_cb"): return
        current = self.thumb_sub_cb.currentText()
        self.thumb_sub_cb.clear()
        for s in self._list_items(self.sub_list): self.thumb_sub_cb.addItem(s)
        target = current or self.cfg.get("thumb_subfolder", "")
        if target and self.thumb_sub_cb.findText(target) >= 0:
            self.thumb_sub_cb.setCurrentText(target)

    def _refresh_preset_combo(self):
        self.preset_cb.clear()
        presets = P.load_presets()
        if presets:
            for name in sorted(presets): self.preset_cb.addItem(name)
        else:
            self.preset_cb.addItem("(no presets saved)")

    def _update_snap_preview(self):
        parts = []
        if self.chk_snap_maxfile.isChecked(): parts.append("scenefile")
        if self.chk_snap_shot.isChecked():    parts.append("shot")
        if self.chk_snap_task.isChecked():    parts.append("task")
        if self.chk_snap_camera.isChecked():  parts.append("cam1")
        self._snap_preview_lbl.setText(f"{'_'.join(parts or ['snapshot'])}_v001.jpg")

    def _load_preset(self):
        name = self.preset_cb.currentText()
        presets = P.load_presets()
        if name in presets: self._apply_cfg_to_form(presets[name])

    def _save_preset_as(self):
        cur = self.preset_cb.currentText()
        name, ok = QtWidgets.QInputDialog.getText(self, "Save preset", "Preset name:",
                                                  text="" if cur == "(no presets saved)" else cur)
        name = name.strip()
        if not (ok and name): return
        presets = P.load_presets()
        if name in presets and QtWidgets.QMessageBox.question(self, "Overwrite Preset",
                f"Preset  '{name}'  already exists. Overwrite?",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel) != QtWidgets.QMessageBox.Ok:
            return
        presets[name] = self._current_form_data()
        P.save_presets(presets)
        self._refresh_preset_combo()
        self.preset_cb.setCurrentText(name)

    def _delete_preset(self):
        name = self.preset_cb.currentText()
        if not name or name == "(no presets saved)": return
        if QtWidgets.QMessageBox.question(self, "Delete Preset", f"Delete preset  '{name}'?",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel) == QtWidgets.QMessageBox.Ok:
            presets = P.load_presets(); presets.pop(name, None); P.save_presets(presets)
            self._refresh_preset_combo()

    def _save_and_accept(self):
        if not self._list_items(self.task_list):
            QtWidgets.QMessageBox.warning(self, "Validation", "At least one task is required."); return
        if not self._list_items(self.sub_list):
            QtWidgets.QMessageBox.warning(self, "Validation", "At least one subfolder is required."); return
        try:
            P.save_cfg(self._current_form_data())     # merges: keeps keys only Max knows about
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Pipeline Setup", f"Could not save the config:\n{e}"); return
        self.accept()
