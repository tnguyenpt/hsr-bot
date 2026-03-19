from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

from missions.launch import run_launch_mvp
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
    parser.add_argument("--run", default="launch_mvp", choices=["launch_mvp"])
    args = parser.parse_args()

    settings = load_settings("config/settings.yaml")
    ensure_dirs(settings)
    configure_logging(settings["app"]["log_file"])

    logging.info("Starting %s", settings["app"]["name"])
    started = datetime.now()

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


if __name__ == "__main__":
    raise SystemExit(main())
