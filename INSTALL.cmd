@echo off
setlocal EnableExtensions
title Whisper Right Ctrl Installer
cd /d "%~dp0"

echo [1/5] Checking Python 3.11...
if not exist ".venv\Scripts\python.exe" (
  where uv.exe >nul 2>nul
  if not errorlevel 1 (
    uv venv --python 3.11 --seed ".venv"
  ) else (
    py -3.11 -m venv ".venv"
  )
  if errorlevel 1 goto :python_missing
)

echo [2/5] Virtual environment is ready.

echo [3/5] Installing packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[test]"
if errorlevel 1 goto :failed

echo [4/5] Running tests...
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto :failed

echo [5/5] Selecting a microphone...
".venv\Scripts\python.exe" -m whisper_right_ctrl.configure
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m whisper_right_ctrl.startup enable --project-root "%CD%"
if errorlevel 1 goto :failed

wscript.exe "%CD%\START_SILENT.vbs"
echo.
echo [SUCCESS] Whisper Right Ctrl is installed and will start at sign-in.
echo The turbo model downloads on the first start.
pause
exit /b 0

:python_missing
echo.
echo Python 3.11 is required. Install Python 3.11 or uv, then run INSTALL.cmd again.
pause
exit /b 2

:failed
echo.
echo [FAILED] Installation did not complete. Copy this window into a GitHub issue.
pause
exit /b 1
