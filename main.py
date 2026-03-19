from __future__ import annotations

import argparse
import importlib
import logging
import os
import sys
from datetime import datetime

from vision.utils import load_settings, ensure_dirs


def configure_logging(log_file: str) -> None:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def send_report_safe(settings: dict, message: str, ok: bool) -> None:
    """Best-effort report sender that won't crash if telegram deps are missing."""
    try:
        from telegram_bot.reporter import send_report
        send_report(settings, message, ok=ok)
    except Exception:
        logging.info("Report skipped (telegram module/env unavailable).")


def preflight_check() -> tuple[bool, str]:
    """Check required runtime modules before importing mission code."""
    required = [
        "pyautogui",
        "cv2",
        "numpy",
        "yaml",
        "PIL",
    ]
    missing = []
    import_errors: list[str] = []

    for mod in required:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            missing.append(mod)
        except Exception as exc:
            import_errors.append(f"{mod}: {exc}")

    if not missing and not import_errors:
        return True, "Runtime dependencies OK"

    pip_names = {
        "pyautogui": "pyautogui",
        "cv2": "opencv-python",
        "numpy": "numpy",
        "yaml": "PyYAML",
        "PIL": "Pillow",
    }

    lines = []
    if missing:
        install_list = " ".join(pip_names[m] for m in missing)
        lines.append("Missing Python modules: " + ", ".join(missing))
        lines.append("Install with:")
        lines.append("  python -m pip install " + install_list)
        lines.append("(or: pip install -r requirements.txt)")

    if import_errors:
        lines.append("Modules installed but failed to import at runtime:")
        lines.extend(f"  - {x}" for x in import_errors)
        lines.append("If running in WSL, ensure GUI/display env is available (DISPLAY/WAYLAND).")

    return False, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="HSR Bot MVP")
    parser.add_argument("--run", default="launch_mvp", choices=["launch_mvp", "stage_a"])
    parser.add_argument("--loops", type=int, default=None, help="Override stage_a loop count")
    args = parser.parse_args()

    settings = load_settings("config/settings.yaml")
    ensure_dirs(settings)
    configure_logging(settings["app"]["log_file"])

    ok_deps, preflight_msg = preflight_check()
    if not ok_deps:
        logging.error("Preflight failed:\n%s", preflight_msg)
        send_report_safe(settings, f"HSR Preflight FAILED\n{preflight_msg}", ok=False)
        return 2

    from missions.launch import run_launch_mvp, close_hsr_apps

    logging.info("Starting %s", settings["app"]["name"])
    started = datetime.now()

    if args.run == "launch_mvp":
        ok, summary = run_launch_mvp(settings)
        finished = datetime.now()
        duration = int((finished - started).total_seconds())
        status = "SUCCESS" if ok else "FAILED"
        message = (
            f"HSR Launch MVP — {status}\n"
            f"Duration: {duration}s\n"
            f"Summary: {summary}"
        )
        send_report_safe(settings, message, ok=ok)
        if ok:
            logging.info("Run completed: %s", summary)
            return 0
        logging.error("Run failed: %s", summary)
        return 1

    # stage_a: repeated launch/login/ready/close cycles
    stage_cfg = settings.get("stage_a", {})
    loops = args.loops if args.loops is not None else int(stage_cfg.get("loops", 10))
    cooldown = int(stage_cfg.get("cooldown_sec", 5))
    stop_on_fail = bool(stage_cfg.get("stop_on_first_failure", True))

    successes = 0
    failures: list[str] = []

    for i in range(1, loops + 1):
        logging.info("Stage A loop %s/%s", i, loops)
        ok, summary = run_launch_mvp(settings)
        if not ok:
            failures.append(f"loop {i}: launch failed — {summary}")
            logging.error("Loop %s failed during launch: %s", i, summary)
            if stop_on_fail:
                break
            continue

        close_ok, close_summary = close_hsr_apps(settings)
        if not close_ok:
            failures.append(f"loop {i}: close failed — {close_summary}")
            logging.error("Loop %s close warning/failure: %s", i, close_summary)
            if stop_on_fail:
                break
        else:
            successes += 1
            logging.info("Loop %s success", i)

        if i < loops:
            import time
            time.sleep(cooldown)

    finished = datetime.now()
    duration = int((finished - started).total_seconds())
    all_ok = successes == loops and not failures

    lines = [
        f"HSR Stage A — {'SUCCESS' if all_ok else 'PARTIAL/FAILED'}",
        f"Duration: {duration}s",
        f"Loops requested: {loops}",
        f"Loops successful: {successes}",
    ]
    if failures:
        lines.append("Failures:")
        lines.extend(f"- {x}" for x in failures[:10])

    message = "\n".join(lines)
    send_report_safe(settings, message, ok=all_ok)

    if all_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
