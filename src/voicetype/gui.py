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
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QTimer, Signal, Slot, QPoint,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QColor, QCursor, QFont, QLinearGradient, QPainter, QPen, QIcon, QAction
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QTextEdit, QVBoxLayout, QWidget, QSystemTrayIcon,
)

from .settings import load_settings, save_settings
from .startup import is_enabled, set_enabled
from .typer import paste_text
from .logger import get_logger

logger = get_logger("gui")

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
        self.recorder = None
        self.transcriber = None
        self.hotkeys = None

        self._state = "idle"
        self._label = "Ready"
        self._tick = 0
        self._drag_start = None
        self._drag_origin = None
        self._history: list[str] = []
        self._tray_icon = None
        self._toast_id = None
        self._is_visible_on_screen = False
        self._startup_complete = False
        self._warmup_started = False

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
        self._err_sig.connect(self._handle_error)

        # 30 fps render loop
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(33)

        if not start_hidden:
            self.slide_down()

        QTimer.singleShot(0, self._finish_startup)

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

        recorder = self._ensure_recorder()
        if recorder.is_recording:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            logger.info("UI: Requesting start recording")
            self._ensure_recorder().start()
            self.slide_down()
            self._set("listening", "Listening…")
        except Exception as e:
            logger.error(f"UI: Failed to start recording: {e}", exc_info=True)
            self.slide_down()
            self._toast("Mic Error")

    def _stop(self):
        try:
            logger.info("UI: Requesting stop recording")
            audio = self._ensure_recorder().stop()
        except Exception as e:
            logger.error(f"UI: Failed to stop recording: {e}", exc_info=True)
            self._toast("Error")
            return
        if not audio:
            logger.warning("UI: No audio data received after stopping.")
            self._toast("No Audio")
            return
        self._set("processing", "Processing…")
        logger.info(f"UI: Starting transcription thread (audio size: {len(audio)} bytes)")
        threading.Thread(target=self._run_whisper, args=(audio,), daemon=True).start()

    def _run_whisper(self, audio: bytes):
        try:
            logger.info("Thread: Running Whisper transcription...")
            text = self._ensure_transcriber().transcribe_bytes(audio, self.settings["model_size"])
            logger.info(f"Thread: Transcription success. Result length: {len(text)}")
            self._done_sig.emit(text)
        except Exception as e:
            logger.error(f"Thread: Transcription error: {e}", exc_info=True)
            self._err_sig.emit(str(e))

    @Slot(str)
    def _handle_error(self, err_msg: str):
        logger.error(f"UI: Received error signal: {err_msg}")
        self._toast("Error")
        # Optional: Show more info in a tooltip or log file if needed

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
            self._ensure_hotkeys().register(hk, lambda: self._hotkey_sig.emit())
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
        if self._tray_icon is not None:
            return

        tray = QSystemTrayIcon(self.windowIcon(), self)
        tray.setToolTip("Voice Typing Assistant")

        menu = QMenu()
        menu.setStyleSheet(_MENU_CSS)

        show_action = QAction("Show Widget", menu)
        show_action.triggered.connect(self._show_from_tray)
        menu.addAction(show_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray_icon = tray

    def _show_from_tray(self):
        QTimer.singleShot(0, self.slide_down)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_from_tray()

    def _ensure_recorder(self):
        if self.recorder is None:
            from .recorder import AudioRecorder
            self.recorder = AudioRecorder()
        return self.recorder

    def _ensure_transcriber(self):
        if self.transcriber is None:
            from .transcriber import WhisperTranscriber
            self.transcriber = WhisperTranscriber()
        return self.transcriber

    def _ensure_hotkeys(self):
        if self.hotkeys is None:
            from .hotkeys import HotkeyManager
            self.hotkeys = HotkeyManager()
        return self.hotkeys

    def _finish_startup(self):
        if self._startup_complete:
            return

        self._start_tray()
        self._register_hotkey()
        self._startup_complete = True
        logger.info("UI: Startup complete")
        self._announce_ready()
        self._start_background_warmup()

    def _announce_ready(self):
        self.slide_down()
        self._toast("I am ready", ms=2500)
        if self._tray_icon and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(
                "Voice Typing Assistant",
                "I am ready",
                QSystemTrayIcon.Information,
                2500,
            )

    def _start_background_warmup(self):
        if self._warmup_started:
            return

        self._warmup_started = True
        model_name = self.settings.get("model_size", "base")
        threading.Thread(
            target=self._warmup_model,
            args=(model_name,),
            daemon=True,
        ).start()

    def _warmup_model(self, model_name: str):
        try:
            logger.info(f"UI: Background warmup started for model {model_name}")
            self._ensure_transcriber().preload_model(model_name)
            logger.info(f"UI: Background warmup finished for model {model_name}")
        except Exception as e:
            logger.warning(f"UI: Background warmup failed: {e}", exc_info=True)

    def _quit(self):
        try:
            if self.hotkeys is not None:
                self.hotkeys.unregister()
        except Exception:
            pass
        if self._tray_icon:
            self._tray_icon.hide()
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
        self.model_cb.currentTextChanged.connect(self._update_model_status)
        form.addRow("Model", self.model_cb)

        self.status_lay = QHBoxLayout()
        self.status_lbl = QLabel("Checking...")
        self.del_btn = QPushButton("Remove")
        self.del_btn.setFixedWidth(70)
        self.del_btn.setStyleSheet("font-size: 10px; padding: 3px;")
        self.del_btn.clicked.connect(self._delete_model)
        self.status_lay.addWidget(self.status_lbl)
        self.status_lay.addWidget(self.del_btn)
        form.addRow("Status", self.status_lay)

        self.hotkey_le = QLineEdit(self._s.get("hotkey", "ctrl+alt+space"))
        form.addRow("Hotkey", self.hotkey_le)

        lay.addLayout(form)
        self._update_model_status()
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

    def _update_model_status(self):
        m = self.model_cb.currentText()
        if self.parent()._ensure_transcriber().is_model_downloaded(m):
            self.status_lbl.setText("Downloaded ✓")
            self.status_lbl.setStyleSheet("color: #3ddc84;")
            self.del_btn.setEnabled(True)
        else:
            self.status_lbl.setText("Not found")
            self.status_lbl.setStyleSheet("color: #a0b0c0;")
            self.del_btn.setEnabled(False)

    def _delete_model(self):
        m = self.model_cb.currentText()
        if self.parent()._ensure_transcriber().delete_model(m):
            self._update_model_status()
            self.parent()._toast("Model Removed")

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
