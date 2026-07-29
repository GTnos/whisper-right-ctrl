@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m whisper_right_ctrl.startup disable
)

powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object CommandLine -Like '*whisper_right_ctrl\app.py*' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo Automatic startup was removed and the running app was stopped.
echo The project folder, model cache, and user configuration were left in place.
pause
