@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run INSTALL.cmd first.
  pause
  exit /b 2
)
".venv\Scripts\python.exe" -m whisper_right_ctrl.configure
pause
