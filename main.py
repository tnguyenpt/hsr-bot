from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

from missions.launch import run_launch_mvp, close_hsr_apps
from telegram_bot.reporter import send_report
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


def main() -> int:
    parser = argparse.ArgumentParser(description="HSR Bot MVP")
    parser.add_argument("--run", default="launch_mvp", choices=["launch_mvp", "stage_a"])
    parser.add_argument("--loops", type=int, default=None, help="Override stage_a loop count")
    args = parser.parse_args()

    settings = load_settings("config/settings.yaml")
    ensure_dirs(settings)
    configure_logging(settings["app"]["log_file"])

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
        send_report(settings, message, ok=ok)
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
    send_report(settings, message, ok=all_ok)

    if all_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
