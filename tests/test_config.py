import json

from whisper_right_ctrl.config import (
    AppConfig,
    MODEL_OPTIONS,
    app_data_dir,
    load_config,
    save_config,
)


def test_app_data_dir_is_portable(tmp_path):
    assert app_data_dir(tmp_path) == tmp_path / "WhisperRightCtrl"


def test_missing_config_uses_safe_defaults(tmp_path):
    config = load_config(tmp_path / "missing.json")
    assert config.input_device is None
    assert config.model == "turbo"
    assert config.device == "cuda"


def test_config_round_trip(tmp_path):
    path = tmp_path / "config.json"
    expected = AppConfig(input_device=7, language="zh")
    save_config(expected, path)
    assert load_config(path) == expected


def test_invalid_config_recovers_to_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")
    assert load_config(path) == AppConfig()


def test_unknown_fields_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"input_device": 3, "private_path": "C:/Users/example"}))
    config = load_config(path)
    assert config.input_device == 3
    assert not hasattr(config, "private_path")


def test_model_options_only_offer_chinese_capable_modes():
    assert MODEL_OPTIONS == (
        ("turbo", "Fast (recommended) - turbo"),
        ("large-v3", "High accuracy - large-v3"),
    )


def test_unsupported_saved_model_falls_back_to_turbo(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"model": "distil-large-v3.5"}), encoding="utf-8")

    assert load_config(path).model == "turbo"
