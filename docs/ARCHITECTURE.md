# Architecture

KnobMixer is split into UI, services, and models.

## Entry point

`main.py` creates the Qt application, initializes services, opens the main window, and shuts services down when the app exits.

## UI

`app/ui/main_window.py` contains the main PyQt6 window. It shows active audio apps, stores user choices, and connects UI actions to services.

`app/ui/styles.py` contains the UI stylesheet.

## Models

`app/models/audio_app.py` describes an audio application/process and matching logic.

## Services

- `audio_service.py` reads and controls Windows audio sessions through pycaw.
- `keyboard_hook_service.py` listens for standard volume keys through a low-level Windows keyboard hook.
- `raw_input_service.py` listens for HID Consumer Control events through Raw Input.
- `settings_service.py` stores settings in JSON.
- `tray_service.py` manages the Windows tray icon and tray menu.
- `autostart_service.py` manages Windows startup through the current-user Run registry key.
- `logger_service.py` configures application logging.

## Runtime data

When running from source, settings and logs are stored in the project folder.

When running as a frozen `.exe`, settings and logs are stored in `%APPDATA%\KnobMixer`.
