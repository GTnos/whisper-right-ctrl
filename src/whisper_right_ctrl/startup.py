from __future__ import annotations

import argparse
import os
from pathlib import Path


ENTRY_NAME = "Whisper Right Ctrl.vbs"


def startup_directory(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ["APPDATA"])
    return base / "Microsoft/Windows/Start Menu/Programs/Startup"


def render_startup_vbs(project_root: Path) -> str:
    root = str(project_root.resolve()).replace('"', '""')
    return f'''Option Explicit
Dim shell, environment, projectRoot, pythonw, application, command
Set shell = CreateObject("WScript.Shell")
projectRoot = "{root}"
pythonw = projectRoot & "\\.venv\\Scripts\\pythonw.exe"
application = projectRoot & "\\src\\whisper_right_ctrl\\app.py"
Set environment = shell.Environment("Process")
environment("PATH") = projectRoot & "\\.venv\\Lib\\site-packages\\nvidia\\cublas\\bin;" & projectRoot & "\\.venv\\Lib\\site-packages\\nvidia\\cudnn\\bin;" & environment("PATH")
shell.CurrentDirectory = projectRoot
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & application & Chr(34)
shell.Run command, 0, False
'''


def enable(project_root: Path, appdata: str | Path | None = None) -> Path:
    directory = startup_directory(appdata)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / ENTRY_NAME
    target.write_text(render_startup_vbs(project_root), encoding="utf-8-sig")
    return target


def disable(appdata: str | Path | None = None) -> Path:
    target = startup_directory(appdata) / ENTRY_NAME
    target.unlink(missing_ok=True)
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
