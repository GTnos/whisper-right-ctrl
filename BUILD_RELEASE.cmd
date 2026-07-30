@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating release validation environment...
  where uv.exe >nul 2>nul
  if not errorlevel 1 (
    uv venv --python 3.11 --seed ".venv"
  ) else (
    py -3.11 -m venv ".venv"
  )
  if errorlevel 1 goto :failed
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[test]"
if errorlevel 1 goto :failed

echo Startup test version:
findstr /C:"portable-path-v2" "tests\test_startup.py"
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto :failed

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$textExtensions=@('.py','.cmd','.vbs','.md','.toml','.yml','.yaml','.txt'); $files=Get-ChildItem -Recurse -File -Force | Where-Object {$_.FullName -notmatch '\\.venv|\\.git|\\dist|\\__pycache__|\\.pytest_cache|\\.egg-info' -and $_.Name -notin @('BUILD_RELEASE.cmd','PUBLISH_GITHUB.cmd') -and $_.Extension -in $textExtensions}; $bad=$files | Select-String -SimpleMatch 'C:\Users\alexw' -List; if($bad){$bad; exit 3}; $stage=Join-Path $env:TEMP 'Whisper-Right-Ctrl-0.3.0'; if(Test-Path $stage){Remove-Item -Recurse -Force -LiteralPath $stage}; New-Item -ItemType Directory $stage | Out-Null; Get-ChildItem -Force | Where-Object {$_.Name -notin @('.venv','.git','dist','BUILD_RELEASE.cmd','PUBLISH_GITHUB.cmd','.pytest_cache') -and $_.Name -notlike '*.egg-info'} | Copy-Item -Destination $stage -Recurse -Force; Get-ChildItem $stage -Recurse -Force | Where-Object {$_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' -or $_.Name -like '*.egg-info'} | Sort-Object FullName -Descending | Remove-Item -Recurse -Force; New-Item -ItemType Directory 'dist' -Force | Out-Null; Compress-Archive -Path $stage -DestinationPath 'dist\Whisper-Right-Ctrl-0.3.0.zip' -Force"
if errorlevel 1 goto :failed

certutil.exe -hashfile "dist\Whisper-Right-Ctrl-0.3.0.zip" SHA256
if errorlevel 1 goto :failed

echo [SUCCESS] Release ZIP created in dist.
pause
exit /b 0

:failed
echo [FAILED] Tests, privacy scan, or packaging failed.
pause
exit /b 1
