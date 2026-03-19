from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui


@dataclass
class MatchResult:
    found: bool
    confidence: float
    center: Optional[Tuple[int, int]] = None


def find_template_on_screen(template_path: str, threshold: float) -> MatchResult:
    screenshot = pyautogui.screenshot()
    screen_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    if template is None:
        return MatchResult(found=False, confidence=0.0, center=None)

    result = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return MatchResult(found=False, confidence=float(max_val), center=None)

    h, w = template.shape[:2]
    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return MatchResult(found=True, confidence=float(max_val), center=(cx, cy))
