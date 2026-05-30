# KnobMixer

[![Build Windows exe](https://github.com/vtaeely/KnobMixer/actions/workflows/build-windows.yml/badge.svg)](https://github.com/vtaeely/KnobMixer/actions/workflows/build-windows.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](#требования)

**KnobMixer** — Windows-приложение для управления громкостью конкретного приложения через клавиши громкости, `Fn`-комбинации, медиакнопки или физический USB-регулятор.

<p align="center">
  <img src="app/assets/icon.png" alt="KnobMixer icon" width="96" height="96">
</p>

## Что делает программа

Обычно клавиши `Volume Up`, `Volume Down`, `Mute`, `Fn`-комбинации громкости и физические регуляторы меняют общую громкость Windows. KnobMixer перехватывает эти события и применяет их к выбранному приложению: Spotify, Discord, браузеру, игре или любому другому процессу с активной аудиосессией.

Пример:

```text
Выбрано: Spotify.exe

Volume Up   -> увеличить громкость только Spotify
Volume Down -> уменьшить громкость только Spotify
Mute        -> включить/выключить mute только у Spotify
```

Изменение общей громкости Windows подавляется по возможности. Полная блокировка master volume не всегда гарантируется из-за ограничений Windows и особенностей некоторых HID-устройств.

## Возможности

- Показывает активные Windows audio sessions.
- Управляет Spotify, Discord, браузерами, играми и другими процессами со звуком.
- Запоминает выбранный процесс по имени.
- Управляет всеми аудиосессиями выбранного процесса.
- Автоматически восстанавливает управление, если процесс закрылся и открылся снова.
- Поддерживает стандартные события `VK_VOLUME_UP`, `VK_VOLUME_DOWN`, `VK_VOLUME_MUTE`.
- Поддерживает `Fn`-комбинации громкости, если клавиатура отправляет стандартные события громкости Windows.
- Поддерживает Raw Input / HID Consumer Control для многих мультимедийных клавиатур, макропадов и USB-регуляторов громкости.
- Перехват регулятора всегда включён; чекбокс в UI намеренно заблокирован.
- Работает в системном трее Windows.
- Хранит настройки в локальном JSON-файле.
- Собирается в standalone `.exe` через PyInstaller.

## Комбинации с Fn

KnobMixer работает с ноутбучными и компактными клавиатурами, где громкость вызывается через сочетания вроде `Fn + F1`, `Fn + F2`, `Fn + F3` или похожие медиакомбинации, если после нажатия клавиатура отправляет стандартные события громкости Windows.

Важно: KnobMixer не перехватывает саму клавишу `Fn` напрямую. На большинстве клавиатур `Fn` обрабатывается прошивкой клавиатуры ещё до того, как Windows получает событие. KnobMixer реагирует на итоговое событие громкости, которое пришло в Windows:

```text
VK_VOLUME_UP
VK_VOLUME_DOWN
VK_VOLUME_MUTE
```

Если клавиатура обрабатывает `Fn`-комбинации полностью на уровне прошивки или отправляет нестандартные HID-события, поведение может зависеть от конкретного устройства. В таком случае Raw Input / HID-режим может увидеть событие громкости, но полное подавление изменения master volume не гарантируется.

## Поддерживаемые устройства

KnobMixer не привязан к одной конкретной клавиатуре или модели регулятора. Он рассчитан на устройства, которые отправляют стандартные события громкости Windows:

- обычные клавиши громкости на клавиатуре;
- ноутбучные `Fn`-комбинации громкости;
- мультимедийные клавиатуры;
- USB-регуляторы громкости;
- макропады;
- HID Consumer Control устройства;
- физические volume knobs, которые отправляют стандартные события громкости.

## Требования

- Windows 10 или Windows 11.
- Python 3.11+ для запуска из исходников.
- Для некоторых устройств или программ, запущенных от администратора, может потребоваться запуск KnobMixer от имени администратора.

## Запуск из исходников

```bat
git clone https://github.com/vtaeely/KnobMixer.git
cd KnobMixer
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Если Python 3.12 не установлен, используй Python 3.11:

```bat
py -3.11 -m venv venv
```

## Сборка exe

```bat
build.bat
```

Готовый файл появится здесь:

```text
dist\KnobMixer.exe
```

## Структура проекта

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

## Как это работает

1. KnobMixer получает список активных аудиосессий Windows через Windows Audio Session API.
2. Пользователь выбирает приложение в интерфейсе или через трей.
3. Программа запоминает имя выбранного процесса.
4. События громкости ловятся через low-level keyboard hook и/или Raw Input.
5. Громкость выбранного процесса меняется через `pycaw`.
6. Если у процесса несколько аудиосессий, управляются все подходящие сессии.
7. Если процесс закрыт, приложение показывает статус, что целевое приложение не найдено.
8. Если процесс снова появился с тем же именем, управление восстанавливается автоматически.

## Используемые технологии

- **PyQt6** — интерфейс приложения.
- **pycaw** — работа с Windows audio sessions.
- **comtypes** — COM-интерфейсы Windows.
- **psutil** — информация о процессах.
- **pywin32** — Raw Input и обработка Windows messages.
- **ctypes** — low-level keyboard hook.
- **PyInstaller** — сборка `.exe`.

## Ограничения

Windows не всегда позволяет полностью заблокировать изменение общей громкости. Особенно это касается устройств, которые отправляют громкость как HID Consumer Control input.

Лучше всего подавление работает со стандартными событиями клавиатуры:

```text
VK_VOLUME_UP
VK_VOLUME_DOWN
VK_VOLUME_MUTE
```

Для USB-регуляторов, мультимедийных устройств и некоторых `Fn`-комбинаций Raw Input может увидеть событие, но Windows всё равно может успеть изменить master volume до того, как KnobMixer обработает ввод.

## Предупреждение про антивирусы

KnobMixer использует Windows keyboard hooks и Raw Input для перехвата клавиш громкости и HID media controls. Некоторые антивирусы могут считать `.exe`, собранный через PyInstaller, подозрительным из-за такого поведения.

Исходный код открыт для проверки, а релизные сборки создаются через GitHub Actions.

## Если что-то не работает

Смотри [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## GitHub Actions

Workflow собирает `KnobMixer.exe` на Windows и загружает его как artifact. После успешной сборки файл можно скачать из последнего workflow run.

Стабильные сборки доступны на странице [Releases](https://github.com/vtaeely/KnobMixer/releases).

## Лицензия

MIT License. Смотри [LICENSE](LICENSE).
