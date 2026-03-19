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
    """Resolve template path across WSL/Linux and native Windows runs."""
    filename = settings["templates"][key]
    templates_cfg = settings.get("templates", {})

    candidates = []

    # Preferred by runtime platform
    if os.name == "nt" and templates_cfg.get("windows_base_dir"):
        candidates.append(str(Path(templates_cfg["windows_base_dir"]) / filename))
    if templates_cfg.get("base_dir"):
        candidates.append(str(Path(templates_cfg["base_dir"]) / filename))

    # Cross-platform fallback candidate
    if templates_cfg.get("windows_base_dir"):
        candidates.append(str(Path(templates_cfg["windows_base_dir"]) / filename))

    for path in candidates:
        if os.path.exists(path):
            return path

    # Return the first candidate even if missing; caller will report low confidence.
    return candidates[0] if candidates else filename
