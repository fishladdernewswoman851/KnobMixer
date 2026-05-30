# Troubleshooting

## The selected app volume changes, but Windows master volume also changes

This can happen with HID Consumer Control devices. KnobMixer can usually receive the event, but Windows may process master volume before the app can suppress it.

Try this order:

1. Select `Keyboard Hook` mode.
2. Restart KnobMixer as administrator.
3. Select `Raw Input / HID` mode.
4. Check the device vendor software and remap the knob to normal volume keys if possible.
5. Test with a normal keyboard volume key to confirm whether the hook works.

## The app is not listed

KnobMixer only shows processes that currently have active Windows audio sessions.

Try:

1. Start audio playback in the target app.
2. Click `Refresh list`.
3. Restart the target app.
4. Restart KnobMixer.

## The app is shown, but volume does not change

Some apps create multiple sessions or recreate sessions after playback changes.

Try:

1. Refresh the session list.
2. Re-select the target process.
3. Restart the target app.
4. Run KnobMixer as administrator if the target app is elevated.

## The tray icon is missing

Check whether KnobMixer is hidden in the Windows tray overflow menu. If needed, enable the icon in Windows taskbar settings.

## Antivirus warning

PyInstaller applications that use keyboard hooks and Windows APIs can sometimes trigger false positives. Build the executable yourself from source if you do not trust a downloaded binary.
