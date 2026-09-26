from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Callable


ENTRY_NAME = "Whisper Right Ctrl.vbs"
SHORTCUT_NAME = "Whisper Right Ctrl.lnk"
START_MENU_FOLDER_NAME = "Whisper Right Ctrl"

ShortcutWriter = Callable[[Path, Path, Path], None]


def startup_directory(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ["APPDATA"])
    return base / "Microsoft/Windows/Start Menu/Programs/Startup"


def start_menu_directory(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ["APPDATA"])
    return base / "Microsoft/Windows/Start Menu/Programs" / START_MENU_FOLDER_NAME


def desktop_directory(userprofile: str | Path | None = None) -> Path:
    base = Path(userprofile or os.environ.get("USERPROFILE", Path.home()))
    return base / "Desktop"


def _powershell_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def write_windows_shortcut(target: Path, launcher: Path, working_directory: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    wscript = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32/wscript.exe"
    arguments = f'"{launcher}"'
    script = (
        "$shell=New-Object -ComObject WScript.Shell;"
        f"$shortcut=$shell.CreateShortcut({_powershell_literal(target)});"
        f"$shortcut.TargetPath={_powershell_literal(wscript)};"
        f"$shortcut.Arguments={_powershell_literal(arguments)};"
        f"$shortcut.WorkingDirectory={_powershell_literal(working_directory)};"
        "$shortcut.Description='Start Whisper Right Ctrl';"
        "$shortcut.Save()"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def render_startup_vbs(project_root: Path) -> str:
    root = str(project_root.resolve()).replace('"', '""')
    return f'''Option Explicit
Dim shell, environment, projectRoot, pythonw, application, command, exitCode
Set shell = CreateObject("WScript.Shell")
projectRoot = "{root}"
pythonw = projectRoot & "\\.venv\\Scripts\\pythonw.exe"
application = projectRoot & "\\src\\whisper_right_ctrl\\app.py"
Set environment = shell.Environment("Process")
environment("PATH") = projectRoot & "\\.venv\\Lib\\site-packages\\nvidia\\cublas\\bin;" & projectRoot & "\\.venv\\Lib\\site-packages\\nvidia\\cudnn\\bin;" & environment("PATH")
shell.CurrentDirectory = projectRoot
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & application & Chr(34)
Do
    exitCode = shell.Run(command, 0, True)
    If exitCode = 75 Then
        WScript.Sleep 1500
    Else
        Exit Do
    End If
Loop
'''


def enable(
    project_root: Path,
    appdata: str | Path | None = None,
    desktop: str | Path | None = None,
    shortcut_writer: ShortcutWriter = write_windows_shortcut,
) -> Path:
    directory = startup_directory(appdata)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / ENTRY_NAME
    target.write_text(render_startup_vbs(project_root), encoding="utf-16")
    root = project_root.resolve()
    launcher = root / "START_SILENT.vbs"
    shortcut_writer(start_menu_directory(appdata) / SHORTCUT_NAME, launcher, root)
    desktop_path = Path(desktop) if desktop is not None else desktop_directory()
    shortcut_writer(desktop_path / SHORTCUT_NAME, launcher, root)
    return target


def disable(
    appdata: str | Path | None = None,
    desktop: str | Path | None = None,
) -> Path:
    target = startup_directory(appdata) / ENTRY_NAME
    target.unlink(missing_ok=True)
    start_menu = start_menu_directory(appdata)
    (start_menu / SHORTCUT_NAME).unlink(missing_ok=True)
    try:
        start_menu.rmdir()
    except OSError:
        pass
    desktop_path = Path(desktop) if desktop is not None else desktop_directory()
    (desktop_path / SHORTCUT_NAME).unlink(missing_ok=True)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("enable", "disable"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    target = (
        enable(args.project_root)
        if args.action == "enable"
        else disable()
    )
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
