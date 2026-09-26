import codecs
from pathlib import Path

from whisper_right_ctrl.startup import (
    SHORTCUT_NAME,
    disable,
    enable,
    render_startup_vbs,
)


TEST_FILE_VERSION = "portable-path-v2"


def write_test_shortcut(target, launcher, working_directory):
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{launcher}\n{working_directory}", encoding="utf-8")


def test_startup_vbs_launches_pythonw_without_cmd():
    portable_root = Path("D:/Portable App")
    script = render_startup_vbs(portable_root)

    assert "pythonw.exe" in script
    assert "app.py" in script
    assert ".cmd" not in script
    assert str(portable_root.resolve()) in script


def test_startup_vbs_restarts_only_for_recoverable_audio_failure():
    script = render_startup_vbs(Path("D:/Portable App"))

    assert "shell.Run(command, 0, True)" in script
    assert "exitCode = 75" in script
    assert "WScript.Sleep 1500" in script


def test_enable_and_disable_are_reversible(tmp_path):
    project_root = tmp_path / "app"
    appdata = tmp_path / "AppData"

    desktop = tmp_path / "Desktop"
    target = enable(
        project_root,
        appdata=appdata,
        desktop=desktop,
        shortcut_writer=write_test_shortcut,
    )
    assert target.exists()
    assert str(project_root.resolve()) in target.read_text(encoding="utf-16")

    disable(appdata=appdata, desktop=desktop)
    assert not target.exists()


def test_enabled_startup_script_uses_windows_script_host_encoding(tmp_path):
    target = enable(
        tmp_path / "app",
        appdata=tmp_path / "AppData",
        desktop=tmp_path / "Desktop",
        shortcut_writer=write_test_shortcut,
    )

    assert target.read_bytes().startswith(codecs.BOM_UTF16_LE)


def test_enable_creates_start_menu_and_desktop_launch_shortcuts(tmp_path):
    project_root = tmp_path / "Portable App"
    appdata = tmp_path / "AppData"
    desktop = tmp_path / "Desktop"
    created = []

    def write_shortcut(target, launcher, working_directory):
        write_test_shortcut(target, launcher, working_directory)
        created.append(target)

    enable(
        project_root,
        appdata=appdata,
        desktop=desktop,
        shortcut_writer=write_shortcut,
    )

    start_menu = appdata / "Microsoft/Windows/Start Menu/Programs/Whisper Right Ctrl" / SHORTCUT_NAME
    desktop_shortcut = desktop / SHORTCUT_NAME
    assert created == [start_menu, desktop_shortcut]
    assert str(project_root / "START_SILENT.vbs") in start_menu.read_text(encoding="utf-8")
    assert str(project_root / "START_SILENT.vbs") in desktop_shortcut.read_text(encoding="utf-8")


def test_disable_removes_startup_and_user_launch_shortcuts(tmp_path):
    appdata = tmp_path / "AppData"
    desktop = tmp_path / "Desktop"
    startup = appdata / "Microsoft/Windows/Start Menu/Programs/Startup/Whisper Right Ctrl.vbs"
    start_menu = appdata / "Microsoft/Windows/Start Menu/Programs/Whisper Right Ctrl" / SHORTCUT_NAME
    desktop_shortcut = desktop / SHORTCUT_NAME
    for target in (startup, start_menu, desktop_shortcut):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("installed", encoding="utf-8")

    disable(appdata=appdata, desktop=desktop)

    assert not startup.exists()
    assert not start_menu.exists()
    assert not desktop_shortcut.exists()
    assert not start_menu.parent.exists()
