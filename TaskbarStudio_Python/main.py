from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QMovie, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QSlider, QVBoxLayout, QHBoxLayout, QFileDialog,
    QColorDialog, QComboBox, QCheckBox, QMessageBox
)

APP_DIR = Path(os.getenv("APPDATA", str(Path.home() / ".config"))) / "TaskbarStudio"
SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULTS = {
    "color": "#263149", "opacity": 82, "height": 64, "radius": 16,
    "gif_path": "", "gif_position": "Right", "gif_size": 42,
    "click_through": True
}


def load_settings():
    settings = DEFAULTS.copy()
    try:
        if SETTINGS_FILE.exists():
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                settings.update(saved)
    except (OSError, json.JSONDecodeError):
        pass
    return settings


def save_settings(settings):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def parse_color(value):
    color = QColor(value.strip())
    return color if color.isValid() else None


def color_css(hex_color, opacity):
    color = parse_color(hex_color) or QColor("#263149")
    alpha = max(0, min(100, int(opacity))) / 100
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.2f})"


class TaskbarOverlay(QWidget):
    """A transparent topmost visual layer over the native Windows taskbar."""

    def __init__(self, settings):
        self.settings = settings.copy()
        flags = (Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.Tool |
                 Qt.WindowType.WindowDoesNotAcceptFocus)
        if self.settings.get("click_through", True):
            flags |= Qt.WindowType.WindowTransparentForInput
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.bar = QFrame(self)
        self.bar.setObjectName("OverlayBar")
        self.gif_label = QLabel(self.bar)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent; border: none;")
        self.movie = None
        self.apply_settings(settings)

    def apply_settings(self, settings):
        self.settings = settings.copy()
        height = max(40, min(130, int(settings["height"])))
        radius = max(0, min(40, int(settings["radius"])))
        self.setStyleSheet(
            f"QFrame#OverlayBar {{ background: {color_css(settings['color'], settings['opacity'])}; "
            f"border-radius: {radius}px; }}"
        )

        screen = QApplication.primaryScreen()
        if screen is not None:
            rect = screen.geometry()
            self.setGeometry(rect.x(), rect.y() + rect.height() - height, rect.width(), height)
            self.bar.setGeometry(0, 0, rect.width(), height)

        self._load_gif(settings.get("gif_path", ""), int(settings.get("gif_size", 42)))

    def _load_gif(self, path, size):
        if self.movie is not None:
            self.movie.stop()
            self.movie.deleteLater()
            self.movie = None
        self.gif_label.clear()
        self.gif_label.hide()

        if path and Path(path).is_file():
            movie = QMovie(path)
            movie.setCacheMode(QMovie.CacheMode.CacheAll)
            movie.setScaledSize(QSize(size, size))
            if movie.isValid():
                self.movie = movie
                self.gif_label.setMovie(movie)
                position = self.settings.get("gif_position", "Right")
                y = max(0, (self.height() - size) // 2)
                if position == "Left":
                    x = 18
                elif position == "Center":
                    x = max(0, (self.width() - size) // 2)
                else:
                    x = max(0, self.width() - size - 22)
                self.gif_label.setGeometry(x, y, size, size)
                self.gif_label.show()
                movie.start()

    def closeEvent(self, event):
        if self.movie is not None:
            self.movie.stop()
        super().closeEvent(event)


class Preview(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("PreviewCard")
        self.bar = QFrame()
        self.bar.setObjectName("PreviewBar")
        self.gif = QLabel("GIF")
        self.gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif.setFixedSize(48, 48)
        self.gif.setStyleSheet("color:#b8b2d8; background:rgba(255,255,255,0.07); border-radius:9px;")
        self.movie = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        heading = QLabel("LIVE DESKTOP PREVIEW")
        heading.setObjectName("Eyebrow")
        layout.addWidget(heading)
        desktop = QFrame()
        desktop.setObjectName("DesktopMock")
        d = QVBoxLayout(desktop)
        d.addStretch(1)
        title = QLabel("Your desktop, your style")
        title.setObjectName("PreviewTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d.addWidget(title)
        tip = QLabel("Adjust the settings and see your taskbar design here")
        tip.setObjectName("Muted")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d.addWidget(tip)
        d.addStretch(2)
        self.bar_layout = QHBoxLayout(self.bar)
        self.bar_layout.setContentsMargins(18, 4, 18, 4)
        self.bar_layout.addWidget(QLabel("☀  81°F"))
        self.bar_layout.addStretch(1)
        self.bar_layout.addWidget(QLabel("⊞      Search      ▣      ▣      ◉"))
        self.bar_layout.addStretch(1)
        self.bar_layout.addWidget(self.gif)
        self.bar_layout.addWidget(QLabel("6:38 PM"))
        d.addWidget(self.bar)
        layout.addWidget(desktop, 1)

    def update(self, settings):
        self.bar.setFixedHeight(int(settings["height"]))
        self.bar.setStyleSheet(
            f"QFrame#PreviewBar {{ background:{color_css(settings['color'], settings['opacity'])}; "
            f"border-radius:{int(settings['radius'])}px; }}"
        )
        path = settings.get("gif_path", "")
        if self.movie is not None:
            self.movie.stop()
            self.movie.deleteLater()
            self.movie = None
        self.gif.clear()
        if path and Path(path).is_file():
            movie = QMovie(path)
            movie.setCacheMode(QMovie.CacheMode.CacheAll)
            movie.setScaledSize(QSize(int(settings["gif_size"]), int(settings["gif_size"])))
            if movie.isValid():
                self.movie = movie
                self.gif.setMovie(movie)
                movie.start()
            else:
                self.gif.setText("GIF")
        else:
            self.gif.setText("GIF")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.overlay = None
        self.setWindowTitle("Taskbar Studio")
        self.resize(1080, 760)
        self.setMinimumSize(920, 660)
        self.setStyleSheet(STYLE)
        self._build()
        self._load_controls()
        self.refresh_preview()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        eyebrow = QLabel("WINDOWS DESKTOP CUSTOMIZATION")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Taskbar Studio")
        title.setObjectName("MainTitle")
        subtitle = QLabel("Give your taskbar a look that feels like yours.")
        subtitle.setObjectName("Muted")
        title_box.addWidget(eyebrow)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top.addLayout(title_box)
        top.addStretch(1)
        self.status = QLabel("READY")
        self.status.setObjectName("Status")
        top.addWidget(self.status, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(360)
        form = QVBoxLayout(card)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(10)
        heading = QLabel("Appearance")
        heading.setObjectName("SectionTitle")
        form.addWidget(heading)

        form.addWidget(QLabel("Background colour (HEX)"))
        color_row = QHBoxLayout()
        self.color_edit = QLineEdit()
        self.color_edit.setPlaceholderText("#263149")
        self.color_edit.editingFinished.connect(self.changed)
        color_row.addWidget(self.color_edit, 1)
        choose = QPushButton("Choose")
        choose.setObjectName("Secondary")
        choose.clicked.connect(self.choose_color)
        color_row.addWidget(choose)
        form.addLayout(color_row)

        self.opacity = self.add_slider(form, "Opacity", 20, 100)
        self.height = self.add_slider(form, "Taskbar height", 40, 130)
        self.radius = self.add_slider(form, "Corner radius", 0, 40)

        gif_heading = QLabel("Animated GIF")
        gif_heading.setObjectName("SectionTitle")
        form.addWidget(gif_heading)
        gif_row = QHBoxLayout()
        self.gif_path_label = QLabel("No GIF selected")
        self.gif_path_label.setObjectName("Muted")
        self.gif_path_label.setWordWrap(True)
        gif_row.addWidget(self.gif_path_label, 1)
        browse = QPushButton("Browse…")
        browse.setObjectName("Secondary")
        browse.clicked.connect(self.choose_gif)
        gif_row.addWidget(browse)
        form.addLayout(gif_row)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("GIF position"))
        self.position = QComboBox()
        self.position.addItems(["Left", "Center", "Right"])
        self.position.currentTextChanged.connect(self.changed)
        pos_row.addWidget(self.position, 1)
        form.addLayout(pos_row)
        self.gif_size = self.add_slider(form, "GIF size", 18, 100)

        self.clickthrough = QCheckBox("Pass clicks through to Windows taskbar")
        self.clickthrough.stateChanged.connect(self.changed)
        form.addWidget(self.clickthrough)

        hint = QLabel(
            "This app draws a translucent overlay above the original Windows taskbar. "
            "It does not patch Explorer or replace Windows system files."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        form.addWidget(hint)
        form.addStretch(1)

        actions = QHBoxLayout()
        apply = QPushButton("Apply overlay")
        apply.clicked.connect(self.apply_overlay)
        hide = QPushButton("Hide overlay")
        hide.setObjectName("Secondary")
        hide.clicked.connect(self.hide_overlay)
        actions.addWidget(apply, 1)
        actions.addWidget(hide)
        form.addLayout(actions)
        save = QPushButton("Save settings")
        save.setObjectName("Ghost")
        save.clicked.connect(self.save_current)
        form.addWidget(save)
        body.addWidget(card)

        right = QVBoxLayout()
        self.preview = Preview()
        right.addWidget(self.preview, 1)
        info = QFrame()
        info.setObjectName("Card")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(18, 16, 18, 16)
        info_title = QLabel("How it works")
        info_title.setObjectName("SectionTitle")
        info_text = QLabel(
            "The overlay sits along the bottom of your primary display. "
            "With click-through enabled, mouse clicks are intended to reach "
            "the real Windows taskbar underneath. Use Hide overlay or close "
            "the app to return to the normal view."
        )
        info_text.setObjectName("Muted")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        right.addWidget(info)
        body.addLayout(right, 1)

    def add_slider(self, layout, label_text, low, high):
        row = QHBoxLayout()
        label = QLabel(label_text)
        value = QLabel(str(low))
        value.setObjectName("Value")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(value)
        layout.addLayout(row)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.valueChanged.connect(lambda n: value.setText(str(n)))
        slider.valueChanged.connect(self.changed)
        layout.addWidget(slider)
        return slider

    def _load_controls(self):
        self.color_edit.setText(self.settings["color"])
        self.opacity.setValue(int(self.settings["opacity"]))
        self.height.setValue(int(self.settings["height"]))
        self.radius.setValue(int(self.settings["radius"]))
        self.gif_size.setValue(int(self.settings["gif_size"]))
        self.position.setCurrentText(self.settings["gif_position"])
        self.clickthrough.setChecked(bool(self.settings["click_through"]))
        path = self.settings.get("gif_path", "")
        self.gif_path_label.setText(Path(path).name if path else "No GIF selected")

    def collect(self):
        color = parse_color(self.color_edit.text())
        if color is None:
            raise ValueError("Enter a valid HEX colour such as #7659ED.")
        return {
            "color": color.name().upper(),
            "opacity": self.opacity.value(),
            "height": self.height.value(),
            "radius": self.radius.value(),
            "gif_path": self.settings.get("gif_path", ""),
            "gif_position": self.position.currentText(),
            "gif_size": self.gif_size.value(),
            "click_through": self.clickthrough.isChecked()
        }

    def changed(self, *_):
        try:
            current = self.collect()
            self.preview.update(current)
            self.status.setText("PREVIEW UPDATED")
            if self.overlay is not None and self.overlay.isVisible():
                self.overlay.apply_settings(current)
        except ValueError:
            self.status.setText("CHECK HEX COLOUR")

    def refresh_preview(self):
        try:
            self.preview.update(self.collect())
        except ValueError:
            pass

    def choose_color(self):
        initial = parse_color(self.color_edit.text()) or QColor("#263149")
        color = QColorDialog.getColor(initial, self, "Choose taskbar colour")
        if color.isValid():
            self.color_edit.setText(color.name().upper())
            self.changed()

    def choose_gif(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose animated GIF", str(Path.home()), "GIF files (*.gif)"
        )
        if path:
            self.settings["gif_path"] = path
            self.gif_path_label.setText(Path(path).name)
            self.changed()

    def apply_overlay(self):
        try:
            current = self.collect()
            self.settings = current
            save_settings(current)
            if self.overlay is not None:
                self.overlay.close()
                self.overlay.deleteLater()
            self.overlay = TaskbarOverlay(current)
            self.overlay.show()
            self.status.setText("OVERLAY ACTIVE")
        except ValueError as error:
            QMessageBox.warning(self, "Invalid setting", str(error))

    def hide_overlay(self):
        if self.overlay is not None:
            self.overlay.hide()
        self.status.setText("OVERLAY HIDDEN")

    def save_current(self):
        try:
            self.settings = self.collect()
            save_settings(self.settings)
            self.status.setText("SETTINGS SAVED")
        except ValueError as error:
            QMessageBox.warning(self, "Invalid setting", str(error))

    def closeEvent(self, event):
        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None
        event.accept()


STYLE = """
QMainWindow, QWidget { background:#10131D; color:#F2F3F8; font-family:'Segoe UI'; font-size:10pt; }
QFrame#Card, QFrame#PreviewCard { background:#191E2B; border:1px solid #2B3245; border-radius:18px; }
QFrame#DesktopMock { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #293650,stop:1 #151B2B); border-radius:13px; }
QFrame#PreviewBar { color:white; }
QLabel#Eyebrow { color:#A99AFF; font-size:9pt; font-weight:700; }
QLabel#MainTitle { color:white; font-size:27pt; font-weight:700; }
QLabel#SectionTitle { color:white; font-size:14pt; font-weight:700; }
QLabel#Muted { color:#A8AFC2; }
QLabel#Value { color:#B9AAFF; font-weight:700; }
QLabel#Status { color:#C7BBFF; background:#292344; border:1px solid #44376D; border-radius:12px; padding:8px 12px; font-weight:700; }
QLabel#PreviewTitle { color:white; font-size:21pt; font-weight:700; }
QLabel#Hint { color:#A8B0C4; background:#202638; border:1px solid #303950; border-radius:10px; padding:10px; font-size:9pt; }
QLineEdit, QComboBox { background:#252C3D; border:1px solid #39435B; border-radius:9px; padding:9px; color:white; }
QPushButton { background:#7659ED; border:0; border-radius:10px; padding:11px 14px; color:white; font-weight:700; }
QPushButton:hover { background:#8A71F5; }
QPushButton#Secondary { background:#2B3347; color:#E4E7F2; }
QPushButton#Ghost { background:transparent; color:#BCB0FF; border:1px solid #4C4279; }
QSlider::groove:horizontal { height:5px; background:#343D52; border-radius:2px; }
QSlider::sub-page:horizontal { background:#8B74F2; border-radius:2px; }
QSlider::handle:horizontal { background:white; width:15px; margin:-6px 0; border-radius:7px; }
QCheckBox { color:#D9DDEC; spacing:8px; }
QCheckBox::indicator { width:17px; height:17px; }
QCheckBox::indicator:unchecked { background:#252C3D; border:1px solid #58627A; border-radius:4px; }
QCheckBox::indicator:checked { background:#7659ED; border:1px solid #A18CFF; border-radius:4px; }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Taskbar Studio")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
