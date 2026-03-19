from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Tuple

from vision.capture import timestamped_screenshot
from vision.detector import find_template_on_screen
from vision.utils import template_path

logger = logging.getLogger(__name__)

ACTIONS_AHK = str(Path(__file__).resolve().parents[1] / "ahk" / "actions.ahk")
DEFAULT_AHK_EXE = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"


def _ahk_exe() -> str:
    return os.getenv("AHK_EXE", DEFAULT_AHK_EXE)


def _ahk(action: str, *args: str) -> None:
    cmd = [_ahk_exe(), ACTIONS_AHK, action, *[str(a) for a in args]]
    subprocess.run(cmd, check=True)


def _wait_for_template(settings: dict, key: str, threshold: float, timeout_sec: int) -> Tuple[bool, tuple | None, float]:
    poll = float(settings["retry"]["template_poll_interval_sec"])
    start = time.time()
    last_conf = 0.0
    while time.time() - start < timeout_sec:
        res = find_template_on_screen(template_path(settings, key), threshold)
        last_conf = max(last_conf, res.confidence)
        if res.found:
            return True, res.center, res.confidence
        time.sleep(poll)
    return False, None, last_conf


def _click(center: tuple[int, int]) -> None:
    _ahk("click", center[0], center[1])


def _unlock_cursor_if_needed(settings: dict) -> None:
    if settings["launch"].get("hold_alt_before_in_game_clicks", True):
        logger.info("Triggering ALT for in-game cursor unlock")
        _ahk("alt_tap")
        time.sleep(0.2)


def _attempt_login(settings: dict) -> bool:
    username = os.getenv("HSR_USERNAME")
    password = os.getenv("HSR_PASSWORD")
    if not username or not password:
        logger.warning("Login screen detected but HSR_USERNAME/HSR_PASSWORD missing")
        return False

    logger.info("Attempting login with env credentials")
    # NOTE: tab order may need tuning after first live test.
    _ahk("press", "Tab")
    _ahk("hotkey", "^a")
    _ahk("type", username)
    _ahk("press", "Tab")
    _ahk("hotkey", "^a")
    _ahk("type", password)
    _ahk("press", "Enter")
    return True


def close_hsr_apps(settings: dict) -> tuple[bool, str]:
    """Best-effort close for HSR and launcher processes on Windows."""
    process_names = settings.get("close", {}).get("process_names", ["StarRail.exe", "launcher.exe"])
    errors: list[str] = []

    for proc in process_names:
        try:
            # Works from WSL when cmd.exe is available.
            result = subprocess.run(
                ["cmd.exe", "/c", "taskkill", "/IM", proc, "/F"],
                capture_output=True,
                text=True,
            )
            if result.returncode not in (0, 128, 255):
                # 128/255 can occur when process is not found depending on environment.
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                combined = stderr or stdout
                if "not found" not in combined.lower() and "no running instance" not in combined.lower():
                    errors.append(f"{proc}: {combined or 'taskkill failed'}")
        except Exception as exc:
            errors.append(f"{proc}: {exc}")

    if errors:
        return False, "; ".join(errors)
    return True, "Closed target processes"


def run_launch_mvp(settings: dict) -> tuple[bool, str]:
    screenshot_dir = settings["app"]["screenshot_dir"]
    ui_thr = float(settings["match_thresholds"]["ui_screen"])
    btn_thr = float(settings["match_thresholds"]["ui_button"])

    launcher_exe = settings["launch"]["launcher_exe"]
    logger.info("Launching HoYoPlay: %s", launcher_exe)
    try:
        subprocess.Popen([launcher_exe], shell=False)
    except FileNotFoundError:
        return False, f"Launcher not found: {launcher_exe}"
    except Exception as exc:
        return False, f"Failed to launch HoYoPlay: {exc}"

    ok, _, conf = _wait_for_template(settings, "hoyoplay_launcher", ui_thr, int(settings["timeouts"]["launcher_visible_sec"]))
    if not ok:
        timestamped_screenshot(screenshot_dir, "launcher-missing")
        return False, f"HoYoPlay launcher not detected (max conf={conf:.3f})"

    login_detected, _, login_conf = _wait_for_template(settings, "saved_info_login", ui_thr, 2)
    if not login_detected:
        login_detected, _, login_conf = _wait_for_template(settings, "hsr_login", ui_thr, 2)

    if login_detected:
        logger.info("Login screen detected (conf=%.3f)", login_conf)
        if not _attempt_login(settings):
            timestamped_screenshot(screenshot_dir, "login-required")
            return False, "Login required but credentials missing"
        time.sleep(3)

    ok, center, conf = _wait_for_template(settings, "hoyoplay_start_button", btn_thr, 20)
    if not ok or not center:
        timestamped_screenshot(screenshot_dir, "start-button-missing")
        return False, f"Start button not found (max conf={conf:.3f})"

    logger.info("Clicking HoYoPlay start button")
    _click(center)

    start_ok_1, _, conf1 = _wait_for_template(settings, "hsr_start_1", ui_thr, 30)
    start_ok_2, _, conf2 = _wait_for_template(settings, "hsr_start_2", ui_thr, 30)
    if not (start_ok_1 or start_ok_2):
        logger.warning("Start screens not confidently detected (%.3f, %.3f)", conf1, conf2)

    _unlock_cursor_if_needed(settings)

    game_ok, _, game_conf = _wait_for_template(settings, "game_default", ui_thr, int(settings["timeouts"]["game_start_sec"]))
    if not game_ok:
        timestamped_screenshot(screenshot_dir, "game-default-missing")
        return False, f"HSR main/default screen not detected (max conf={game_conf:.3f})"

    timestamped_screenshot(screenshot_dir, "launch-mvp-success")
    return True, "HoYoPlay launch/login succeeded, HSR default screen detected"
