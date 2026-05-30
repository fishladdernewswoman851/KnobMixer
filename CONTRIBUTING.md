# Contributing

## Development setup

```bat
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
python main.py
```

## Before opening a pull request

Run:

```bat
python -m compileall app main.py
```

For Windows-specific behavior, test with:

- normal keyboard volume keys;
- a multimedia keyboard;
- a USB volume knob or HID Consumer Control device when available.

## Pull request rules

- Do not commit `venv`, `build`, `dist`, `release`, `settings.json`, logs, or `__pycache__`.
- Keep Windows-specific limitations documented clearly.
- Avoid promising complete suppression of master volume for all HID devices.
