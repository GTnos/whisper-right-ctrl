from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path


APP_DIRECTORY_NAME = "WhisperRightCtrl"


@dataclass
class AppConfig:
    input_device: int | str | None = None
    input_device_name: str | None = None
    language: str | None = "zh"
    model: str = "turbo"
    device: str = "cuda"
    compute_type: str = "float16"
    minimum_seconds: float = 0.25
    restore_clipboard: bool = True


def app_data_dir(local_app_data: str | Path | None = None) -> Path:
    base = Path(local_app_data or os.environ.get("LOCALAPPDATA", Path.home()))
    return base / APP_DIRECTORY_NAME


def config_path(local_app_data: str | Path | None = None) -> Path:
    return app_data_dir(local_app_data) / "config.json"


def log_path(local_app_data: str | Path | None = None) -> Path:
    return app_data_dir(local_app_data) / "voice-input.log"


def load_config(path: Path | None = None) -> AppConfig:
    target = path or config_path()
    if not target.exists():
        return AppConfig()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
        allowed = {item.name for item in fields(AppConfig)}
        values = {key: value for key, value in raw.items() if key in allowed}
        return AppConfig(**values)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return AppConfig()


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, target)
    return target
