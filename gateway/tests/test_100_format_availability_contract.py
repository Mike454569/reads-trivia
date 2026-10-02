"""Prevent built formats from being advertised while their runtime flag is off/missing."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CONFIG = (ROOT / "reads-config.js").read_text(encoding="utf-8")


def _app_engine_flags():
    return set(re.findall(r"READS_CONFIG\.(enableEngine[A-Za-z0-9]+)\s*===\s*true", APP))


def _production_engine_flags():
    return {
        name: value == "true"
        for name, value in re.findall(
            r"(enableEngine[A-Za-z0-9]+)\s*:\s*(true|false)", CONFIG
        )
    }


def test_every_app_engine_flag_exists_in_production_config():
    app_flags = _app_engine_flags()
    config_flags = _production_engine_flags()
    missing = sorted(app_flags - set(config_flags))
    assert missing == [], f"app references engine flags missing from reads-config.js: {missing}"


def test_every_built_engine_family_is_enabled_for_100_format_rollout():
    app_flags = _app_engine_flags()
    config_flags = _production_engine_flags()
    disabled = sorted(name for name in app_flags if config_flags.get(name) is not True)
    assert disabled == [], f"built game families still disabled in production config: {disabled}"
