# KnobMixer

[![Build Windows exe](https://github.com/vtaeely/KnobMixer/actions/workflows/build-windows.yml/badge.svg)](https://github.com/vtaeely/KnobMixer/actions/workflows/build-windows.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](#requirements)

**KnobMixer** is a Windows per-app volume controller. It redirects keyboard volume keys, media buttons, and supported USB volume knobs to one selected application instead of changing the Windows master volume.

<p align="center">
  <img src="app/assets/icon.png" alt="KnobMixer icon" width="96" height="96">
</p>

## What it does

Normally, `Volume Up`, `Volume Down`, `Mute`, and many physical knobs control the global Windows volume. KnobMixer listens for those controls and applies them to the selected audio application, such as Spotify, Discord, a browser, or a game.

Example:

```text
Selected app: Spotify.exe

Volume Up   -> increase only Spotify volume
Volume Down -> decrease only Spotify volume
Mute        -> toggle only Spotify mute
```

KnobMixer tries to suppress changes to Windows master volume when possible. This is best-effort behavior because Windows and some HID Consumer Control devices do not always allow full suppression.

## Features

- Lists active Windows audio sessions.
- Controls Spotify, Discord, browsers, games, and other processes with active audio sessions.
- Remembers the selected process by name.
- Controls all audio sessions that belong to the selected process.
- Automatically resumes control when the process closes and opens again.
- Supports standard `VK_VOLUME_UP`, `VK_VOLUME_DOWN`, and `VK_VOLUME_MUTE` keyboard events.
- Supports Raw Input / HID Consumer Control devices for many multimedia keyboards, macro pads, and USB volume knobs.
- Always-on volume intercept: the UI checkbox is locked on intentionally.
- Runs in the Windows system tray.
- Stores settings in a local JSON file.
- Builds into a standalone `.exe` with PyInstaller.

## Requirements

- Windows 10 or Windows 11
- Python 3.11+ for source mode
- Administrator mode may be required for some devices or elevated target applications

## Quick start from source

```bat
git clone https://github.com/vtaeely/KnobMixer.git
cd KnobMixer
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If Python 3.12 is not installed, use Python 3.11:

```bat
py -3.11 -m venv venv
```

## Build Windows exe

```bat
build.bat
```

The executable will be created here:

```text
dist\KnobMixer.exe
```

## Project structure

```text
KnobMixer/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   │   └── build-windows.yml
│   └── pull_request_template.md
├── app/
│   ├── assets/
│   ├── models/
│   ├── services/
│   └── ui/
├── docs/
├── logs/
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── build.bat
├── run.bat
├── KnobMixer.spec
├── CHANGELOG.md
├── LICENSE
├── README.ru.md
└── README.md
```

## How it works

1. KnobMixer reads active Windows audio sessions through Windows Audio Session API.
2. The user selects an app from the UI or tray menu.
3. KnobMixer stores the selected process name.
4. Volume events are captured through a low-level keyboard hook and/or Raw Input.
5. The selected process volume is changed through `pycaw`.
6. If the process has multiple audio sessions, all matching sessions are controlled.
7. If the process is not running, the app shows that the target application was not found.
8. When the process appears again with the same name, control resumes automatically.

## Technologies

- **PyQt6** for the desktop UI.
- **pycaw** for Windows audio sessions.
- **comtypes** for Windows COM interop.
- **psutil** for process information.
- **pywin32** for Raw Input and Windows message handling.
- **ctypes** for the low-level keyboard hook.
- **PyInstaller** for one-file Windows builds.

## Limitations

Windows does not always allow an application to fully suppress master volume changes. This is especially common with devices that send volume events as HID Consumer Control input.

Best suppression behavior usually happens with standard keyboard events:

```text
VK_VOLUME_UP
VK_VOLUME_DOWN
VK_VOLUME_MUTE
```

For USB knobs or multimedia devices, Raw Input can receive the event, but the system volume may still change before KnobMixer can react.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Build artifacts

GitHub Actions builds `KnobMixer.exe` on Windows and uploads it as a workflow artifact. Open the latest successful workflow run and download `KnobMixer-windows`.

## License

MIT License. See [LICENSE](LICENSE).
