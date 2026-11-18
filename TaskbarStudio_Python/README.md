# Taskbar Studio — Python Edition

**This version is entirely Python.** The WPF/C# project and Python HTTP backend have been removed.

## Features
- Modern dark desktop interface using PySide6.
- Taskbar background HEX colour and colour picker.
- Opacity, height and rounded-corner controls.
- Animated GIF selection, size and left/centre/right positioning.
- Live preview in the editor.
- Apply/hide a transparent always-on-top overlay.
- Optional click-through mode so mouse clicks can reach the original Windows taskbar.
- Settings saved to `%APPDATA%\TaskbarStudio\settings.json`.

## Requirements
- Windows 10 or Windows 11
- Python 3.10 or newer

## Run
Double-click `run.bat`, or open PowerShell in this folder and run:

```powershell
py -3 -m pip install -r requirements.txt
py -3 main.py
```

## Important
This app creates a translucent, borderless overlay along the bottom of the primary display. It does not patch Windows Explorer, replace the Windows taskbar, or modify system files. With click-through enabled, mouse clicks are intended to pass through the overlay to the native taskbar underneath.

The overlay is designed for a standard horizontal taskbar at the bottom of the primary monitor. Multi-monitor layouts, top/side taskbars, and changes to Windows shell layering are not currently handled.

Use **Hide overlay** or close the app to dismiss the overlay.
