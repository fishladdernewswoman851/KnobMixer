@echo off
setlocal

cd /d "%~dp0"

if not exist logs mkdir logs
echo [%date% %time%] Build started>>logs\app.log

if not exist venv\Scripts\python.exe (
    py -3.12 -m venv venv >>logs\app.log 2>&1
)

if not exist venv\Scripts\python.exe (
    py -3.11 -m venv venv >>logs\app.log 2>&1
)

if not exist venv\Scripts\python.exe (
    python -m venv venv >>logs\app.log 2>&1
)

if not exist venv\Scripts\python.exe (
    echo Failed to create virtual environment.>>logs\app.log
    echo Failed to create virtual environment. See logs\app.log.
    exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.>>logs\app.log
    echo Failed to activate virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip >>logs\app.log 2>&1
if errorlevel 1 (
    echo Failed to upgrade pip. See logs\app.log.
    exit /b 1
)

pip install -r requirements.txt -r requirements-dev.txt >>logs\app.log 2>&1
if errorlevel 1 (
    echo Failed to install requirements. See logs\app.log.
    exit /b 1
)

python -m PyInstaller --noconfirm KnobMixer.spec >>logs\app.log 2>&1
if errorlevel 1 (
    echo PyInstaller build failed. See logs\app.log.
    exit /b 1
)

echo [%date% %time%] Build finished: dist\KnobMixer.exe>>logs\app.log
echo Built dist\KnobMixer.exe
endlocal
