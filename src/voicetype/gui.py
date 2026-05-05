"""
gui.py – Dynamic-Island-style floating pill widget.
Built with PySide6 for premium anti-aliased rendering.
Tiny, curved, sits at the top of the screen, never blocks content.
Features smooth slide-down/fade-in animations.
"""

import math
import sys
import threading
from pathlib import Path

import pyperclip
import pystray
from PIL import Image as PILImage, ImageDraw as PILDraw
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QTimer, Signal, Slot, QPoint,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QColor, QCursor, QFont, QLinearGradient, QPainter, QPen, QIcon
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from .hotkeys import HotkeyManager
from .recorder import AudioRecorder
from .settings import load_settings, save_settings
from .startup import is_enabled, set_enabled
from .transcriber import WhisperTranscriber
from .typer import paste_text

# ── Layout constants ────────────────────────────────────────────────────
PILL_W, PILL_H = 190, 38
PAD = 10
WIN_W, WIN_H = PILL_W + PAD * 2, PILL_H + PAD * 2

# ── Colour palette ──────────────────────────────────────────────────────
BG = QColor("#0d1117")
BG2 = QColor("#111820")
BORDER = QColor("#1c2b3a")
TXT = QColor("#d0dae6")
TXT_DIM = QColor("#5a7085")
TEAL = QColor("#20d5c3")
AMBER = QColor("#f7a531")
BLUE = QColor("#4a9eca")
GREEN = QColor("#3ddc84")


# ═══════════════════════════════════════════════════════════════════════
#  Main pill widget
# ═══════════════════════════════════════════════════════════════════════
class PillWidget(QWidget):
    _hotkey_sig = Signal()
    _done_sig = Signal(str)
    _err_sig = Signal(str)

    def __init__(self, start_hidden=False):
        super().__init__()
        self.settings = load_settings()
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.hotkeys = HotkeyManager()

        self._state = "idle"
        self._label = "Ready"
        self._tick = 0
        self._drag_start = None
        self._drag_origin = None
        self._history: list[str] = []
        self._tray_icon = None
        self._toast_id = None
        self._is_visible_on_screen = False

        # Window flags: frameless, topmost, hidden from taskbar, transparent
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Position at top-centre of screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.center_x = screen.center().x() - WIN_W // 2
        self.visible_y = 8
        self.hidden_y = -WIN_H - 20  # Off-screen above

        # Start hidden by default
        self.move(self.center_x, self.hidden_y)
        self.setWindowOpacity(0.0)

        # Animation Group
        self.anim_group = QParallelAnimationGroup(self)
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim_group.addAnimation(self.pos_anim)
        self.anim_group.addAnimation(self.opacity_anim)

        # Signals (thread-safe Qt bridge)
        self._hotkey_sig.connect(self.toggle_recording)
        self._done_sig.connect(self._handle_result)
        self._err_sig.connect(lambda e: self._toast("Error"))

        # 30 fps render loop
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(33)

        self._register_hotkey()
        self._start_tray()

        if not start_hidden:
            self.slide_down()

    # ── Slide Animations ────────────────────────────────────────────────
    def slide_down(self):
        if self._is_visible_on_screen:
            return
        self._is_visible_on_screen = True
        self.show()

        self.anim_group.stop()
        
        # Position animation (Slide down)
        self.pos_anim.setDuration(450)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(self.pos().x(), self.visible_y))
        self.pos_anim.setEasingCurve(QEasingCurve.OutBack) # Slight bounce effect
        
        # Opacity animation (Fade in)
        self.opacity_anim.setDuration(350)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutQuad)

        self.anim_group.start()

    def slide_up(self):
        if not self._is_visible_on_screen:
            return
        self._is_visible_on_screen = False

        self.anim_group.stop()

        # Position animation (Slide up)
        self.pos_anim.setDuration(400)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(self.pos().x(), self.hidden_y))
        self.pos_anim.setEasingCurve(QEasingCurve.InBack)
        
        # Opacity animation (Fade out)
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.InQuad)

        self.anim_group.start()

    # ── Painting ────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        pill = QRectF(PAD, PAD, PILL_W, PILL_H)
        rad = PILL_H / 2.0
        pulse = math.sin(self._tick * 0.12) * 0.5 + 0.5

        # Pick accent colour
        if self._state == "listening":
            accent = TEAL
        elif self._state == "processing":
            accent = AMBER
        else:
            accent = BLUE

        # ── Outer glow layers ───────────────────────────────────────────
        for i in range(5, 0, -1):
            a = int((18 + pulse * 25) * (1 - i / 6))
            if self._state == "idle":
                a = a // 4
            c = QColor(accent)
            c.setAlpha(max(a, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            g = pill.adjusted(-i * 1.6, -i * 1.6, i * 1.6, i * 1.6)
            p.drawRoundedRect(g, rad + i * 1.6, rad + i * 1.6)

        # ── Pill body (gradient) ────────────────────────────────────────
        grad = QLinearGradient(pill.topLeft(), pill.bottomLeft())
        grad.setColorAt(0, BG)
        grad.setColorAt(1, BG2)
        p.setBrush(grad)
        bc = QColor(accent)
        bc.setAlpha(55 + int(pulse * 45) if self._state != "idle" else 25)
        p.setPen(QPen(bc, 1.2))
        p.drawRoundedRect(pill, rad, rad)

        # ── Status dot ──────────────────────────────────────────────────
        dot_cx = PAD + 20.0
        dot_cy = PAD + PILL_H / 2.0
        if self._state == "listening":
            dot_r = 5.0 + pulse * 2.5
        elif self._state == "processing":
            dot_r = 5.0 + ((self._tick % 30) / 30.0) * 2.0
        else:
            dot_r = 4.0 + pulse * 0.8

        # dot glow
        gc = QColor(accent)
        gc.setAlpha(45)
        p.setPen(Qt.NoPen)
        p.setBrush(gc)
        p.drawEllipse(QPointF(dot_cx, dot_cy), dot_r + 4, dot_r + 4)
        # dot core
        p.setBrush(accent)
        p.drawEllipse(QPointF(dot_cx, dot_cy), dot_r, dot_r)

        # ── Label text ──────────────────────────────────────────────────
        text_rect = QRectF(PAD + 36, PAD, PILL_W - 46, PILL_H)
        p.setPen(TXT if self._state != "idle" else TXT_DIM)
        p.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._label)

        p.end()

    # ── Animation ───────────────────────────────────────────────────────
    def _on_tick(self):
        self._tick += 1
        self.update()

    # ── Mouse: click to record, drag to move, right-click for menu ──────
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_start = ev.globalPosition().toPoint()
            self._drag_origin = self.pos()
        elif ev.button() == Qt.RightButton:
            self._ctx_menu(ev.globalPosition().toPoint())

    def mouseMoveEvent(self, ev):
        if self._drag_start and (ev.buttons() & Qt.LeftButton):
            delta = ev.globalPosition().toPoint() - self._drag_start
            self.move(self._drag_origin + delta)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self._drag_start:
            moved = (ev.globalPosition().toPoint() - self._drag_start).manhattanLength()
            if moved < 6:
                self.toggle_recording()
            self._drag_start = None

    # ── Context menu ────────────────────────────────────────────────────
    def _ctx_menu(self, pos):
        m = QMenu(self)
        m.setStyleSheet(_MENU_CSS)
        mode = "Auto-Paste ✓" if self.settings["auto_paste"] else "Copy-Only ✓"
        m.addAction(f"Mode: {mode}", self._flip_mode)
        m.addAction("Copy Last", self._copy_last)
        m.addSeparator()
        m.addAction("Settings…", self._open_settings)
        m.addAction("History…", self._open_history)
        m.addSeparator()
        m.addAction("Hide Widget", self.slide_up)
        m.addAction("Quit", self._quit)
        m.exec(pos)

    def _flip_mode(self):
        self.settings["auto_paste"] = not self.settings["auto_paste"]
        save_settings(self.settings)
        tag = "Auto-Paste" if self.settings["auto_paste"] else "Copy-Only"
        self._toast(tag)

    def _copy_last(self):
        if self._history:
            pyperclip.copy(self._history[-1])
            self._toast("Copied ✓")
        else:
            self._toast("Nothing")

    # ── Recording workflow ──────────────────────────────────────────────
    @Slot()
    def toggle_recording(self):
        # If widget is hidden and hotkey is pressed, start recording
        if not self._is_visible_on_screen:
            self._start()
            return

        if self.recorder.is_recording:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            self.recorder.start()
            self.slide_down()
            self._set("listening", "Listening…")
        except Exception as e:
            self.slide_down()
            self._toast("Mic Error")

    def _stop(self):
        try:
            audio = self.recorder.stop()
        except Exception:
            self._toast("Error")
            return
        if not audio:
            self._toast("No Audio")
            return
        self._set("processing", "Processing…")
        threading.Thread(target=self._run_whisper, args=(audio,), daemon=True).start()

    def _run_whisper(self, audio: bytes):
        try:
            text = self.transcriber.transcribe_bytes(audio, self.settings["model_size"])
            self._done_sig.emit(text)
        except Exception as e:
            self._err_sig.emit(str(e))

    @Slot(str)
    def _handle_result(self, text: str):
        if text:
            self._history.append(text)
            if len(self._history) > 50:
                self._history = self._history[-50:]
        if text and self.settings["auto_paste"]:
            paste_text(text)
            self._toast("Inserted ✓")
        elif text:
            pyperclip.copy(text)
            self._toast("Copied ✓")
        else:
            self._toast("No speech")

    # ── State helpers ───────────────────────────────────────────────────
    def _set(self, state, label):
        self._state = state
        self._label = label
        self.update()

    def _toast(self, label, ms=2000):
        self._set("idle", label)
        if self._toast_id is not None:
            self.killTimer(self._toast_id)
        self._toast_id = self.startTimer(ms)

    def timerEvent(self, ev):
        if ev.timerId() == self._toast_id:
            self.killTimer(self._toast_id)
            self._toast_id = None
            self._set("idle", "Ready")
            # Automatically hide the widget after the toast disappears
            self.slide_up()

    # ── Hotkey ──────────────────────────────────────────────────────────
    def _register_hotkey(self):
        hk = self.settings.get("hotkey", "ctrl+alt+space")
        try:
            self.hotkeys.register(hk, lambda: self._hotkey_sig.emit())
        except Exception:
            pass

    # ── Settings dialog ─────────────────────────────────────────────────
    def _open_settings(self):
        self.slide_down()
        dlg = _SettingsDialog(self.settings, self)
        if dlg.exec():
            self.settings = dlg.result_settings()
            save_settings(self.settings)
            self.hotkeys.unregister()
            self._register_hotkey()
            set_enabled(self.settings.get("start_with_windows", False))
            self._toast("Saved ✓")

    # ── History dialog ──────────────────────────────────────────────────
    def _open_history(self):
        self.slide_down()
        dlg = _HistoryDialog(self._history, self)
        dlg.exec()

    # ── Tray icon ───────────────────────────────────────────────────────
    def _start_tray(self):
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            img = PILImage.open(icon_path).convert("RGBA")
            img = img.resize((64, 64), PILImage.Resampling.LANCZOS)
        else:
            img = PILImage.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = PILDraw.Draw(img)
            d.rounded_rectangle((8, 8, 56, 56), radius=16, fill=(16, 23, 32))
            d.ellipse((20, 20, 44, 44), fill=(32, 213, 195))
            d.ellipse((27, 27, 37, 37), fill=(13, 17, 23))
        menu = pystray.Menu(
            pystray.MenuItem("Show Widget", lambda *a: self._show_from_tray(), default=True),
            pystray.MenuItem("Settings", lambda *a: QTimer.singleShot(0, self._open_settings)),
            pystray.MenuItem("Quit", lambda *a: QTimer.singleShot(0, self._quit)),
        )
        self._tray_icon = pystray.Icon("vta", img, "Voice Typing Assistant", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _show_from_tray(self):
        QTimer.singleShot(0, self.slide_down)

    def _quit(self):
        try:
            self.hotkeys.unregister()
        except Exception:
            pass
        if self._tray_icon:
            self._tray_icon.stop()
        QApplication.quit()


# ═══════════════════════════════════════════════════════════════════════
#  Settings dialog – small, dark, matching the pill aesthetic
# ═══════════════════════════════════════════════════════════════════════
_DLG_CSS = """
QDialog { background: #0d1117; }
QLabel  { color: #a0b0c0; font-family: 'Segoe UI'; font-size: 12px; }
QLineEdit, QComboBox {
    background: #161d27; color: #d0dae6; border: 1px solid #1c2b3a;
    border-radius: 6px; padding: 5px 8px; font-family: 'Segoe UI';
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #161d27; color: #d0dae6; selection-background-color: #1c2b3a;
}
QCheckBox { color: #a0b0c0; font-family: 'Segoe UI'; spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #1c2b3a; background: #161d27; }
QCheckBox::indicator:checked { background: #20d5c3; border-color: #20d5c3; }
QPushButton {
    background: #161d27; color: #d0dae6; border: 1px solid #1c2b3a;
    border-radius: 8px; padding: 7px 18px; font-family: 'Segoe UI'; font-weight: 600;
}
QPushButton:hover { background: #1c2b3a; }
QPushButton#save { background: #20d5c3; color: #0d1117; border: none; }
QPushButton#save:hover { background: #18b8a8; }
"""


class _SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(320, 280)
        self.setStyleSheet(_DLG_CSS)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._s = dict(settings)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 14)

        title = QLabel("⚙  Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e8f0;")
        lay.addWidget(title)
        lay.addSpacing(8)

        form = QFormLayout()
        form.setSpacing(10)

        self.model_cb = QComboBox()
        self.model_cb.addItems(["tiny", "base", "small"])
        self.model_cb.setCurrentText(self._s.get("model_size", "base"))
        form.addRow("Model", self.model_cb)

        self.hotkey_le = QLineEdit(self._s.get("hotkey", "ctrl+alt+space"))
        form.addRow("Hotkey", self.hotkey_le)

        lay.addLayout(form)
        lay.addSpacing(6)

        self.startup_chk = QCheckBox("Start with Windows")
        self.startup_chk.setChecked(is_enabled())
        lay.addWidget(self.startup_chk)

        self.paste_chk = QCheckBox("Auto-paste into active field")
        self.paste_chk.setChecked(self._s.get("auto_paste", True))
        lay.addWidget(self.paste_chk)

        lay.addStretch()

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        lay.addLayout(btns)

    def result_settings(self) -> dict:
        s = dict(self._s)
        s["model_size"] = self.model_cb.currentText()
        s["hotkey"] = self.hotkey_le.text().strip() or "ctrl+alt+space"
        s["start_with_windows"] = self.startup_chk.isChecked()
        s["auto_paste"] = self.paste_chk.isChecked()
        return s


# ═══════════════════════════════════════════════════════════════════════
#  History dialog
# ═══════════════════════════════════════════════════════════════════════
class _HistoryDialog(QDialog):
    def __init__(self, history: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setFixedSize(380, 280)
        self.setStyleSheet(_DLG_CSS)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 12)

        title = QLabel("☰  Recent Transcripts")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e8f0;")
        lay.addWidget(title)

        box = QTextEdit()
        box.setReadOnly(True)
        box.setStyleSheet(
            "QTextEdit { background: #0f1520; color: #b0c0d0; border: 1px solid #1c2b3a;"
            " border-radius: 8px; padding: 8px; font-family: 'Segoe UI'; font-size: 12px; }"
        )
        if history:
            for i, t in enumerate(reversed(history), 1):
                box.append(f"[{i}]  {t}\n")
        else:
            box.setPlainText("No transcripts yet.")
        lay.addWidget(box)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        blay = QHBoxLayout()
        blay.addStretch()
        blay.addWidget(close_btn)
        lay.addLayout(blay)


# ── Context-menu stylesheet ────────────────────────────────────────────
_MENU_CSS = """
QMenu {
    background: #0d1117; color: #d0dae6; border: 1px solid #1c2b3a;
    border-radius: 8px; padding: 6px 0;
    font-family: 'Segoe UI'; font-size: 12px;
}
QMenu::item { padding: 6px 28px 6px 14px; }
QMenu::item:selected { background: #1c2b3a; }
QMenu::separator { height: 1px; background: #1c2b3a; margin: 4px 10px; }
"""


# ═══════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════
def main():
    import argparse
    parser = argparse.ArgumentParser()
    # By default we start hidden now, so the flag doesn't do much,
    # but we keep it for backward compatibility
    parser.add_argument("--background", action="store_true")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Start hidden unless overridden
    widget = PillWidget(start_hidden=True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
