from __future__ import annotations

import asyncio
import logging
import os

from telegram import Bot

logger = logging.getLogger(__name__)


async def _send(token: str, chat_id: str, text: str) -> None:
    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=text)


def send_report(settings: dict, message: str, ok: bool) -> None:
    telegram_cfg = settings.get("telegram", {})
    if ok and not telegram_cfg.get("notify_on_success", True):
        return
    if (not ok) and not telegram_cfg.get("notify_on_failure", True):
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.info("Telegram env vars not set; skipping report.\n%s", message)
        return

    try:
        asyncio.run(_send(token, chat_id, message))
    except Exception as exc:
        logger.exception("Failed to send Telegram message: %s", exc)
