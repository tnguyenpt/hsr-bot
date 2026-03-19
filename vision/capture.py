from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pyautogui


def screenshot(path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img = pyautogui.screenshot()
    img.save(path)
    return path


def timestamped_screenshot(output_dir: str, prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = str(Path(output_dir) / f"{prefix}-{ts}.png")
    return screenshot(path)
