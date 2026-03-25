import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def handle_message(message: dict) -> None:
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            code = parts[1]
            logger.info("Received /start with code %s from chat %s", code, chat_id)
        else:
            await send_message(
                chat_id, "Добро пожаловать в Matrix! Используйте код из профиля: /start <код>"
            )
    elif text.startswith("/help"):
        help_text = (
            "Matrix — платформа управления компетенциями.\n/start <код> — привязка аккаунта"
        )
        await send_message(chat_id, help_text)


async def send_message(chat_id: int, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


async def poll() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, bot disabled")
        while True:
            await asyncio.sleep(60)

    offset = 0
    async with httpx.AsyncClient(timeout=httpx.Timeout(35.0)) as client:
        while True:
            try:
                params = {"offset": offset, "timeout": 30}
                resp = await client.get(f"{BASE_URL}/getUpdates", params=params)
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        await handle_message(update["message"])
            except Exception:
                logger.exception("Telegram polling error")
                await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(poll())
