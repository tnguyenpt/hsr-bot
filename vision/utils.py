from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def load_settings(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(settings: Dict[str, Any]) -> None:
    screenshot_dir = settings["app"]["screenshot_dir"]
    log_file = settings["app"]["log_file"]
    os.makedirs(screenshot_dir, exist_ok=True)
    os.makedirs(Path(log_file).parent, exist_ok=True)


def template_path(settings: Dict[str, Any], key: str) -> str:
    base = settings["templates"]["base_dir"]
    filename = settings["templates"][key]
    return str(Path(base) / filename)
