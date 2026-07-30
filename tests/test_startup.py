import codecs
from pathlib import Path

from whisper_right_ctrl.startup import disable, enable, render_startup_vbs


TEST_FILE_VERSION = "portable-path-v2"


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

    target = enable(project_root, appdata=appdata)
    assert target.exists()
    assert str(project_root.resolve()) in target.read_text(encoding="utf-16")

    disable(appdata=appdata)
    assert not target.exists()


def test_enabled_startup_script_uses_windows_script_host_encoding(tmp_path):
    target = enable(tmp_path / "app", appdata=tmp_path / "AppData")

    assert target.read_bytes().startswith(codecs.BOM_UTF16_LE)
