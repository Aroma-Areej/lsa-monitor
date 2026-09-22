"""
Charles Plumbing Services Ltd - Google listing "Message" button monitor
------------------------------------------------------------------------
GitHub Actions version: ye script EK BAAR chalta hai aur exit ho jata hai.
GitHub Actions khud isay har 5 minute (schedule ke mutabiq) dobara trigger karta hai.

Zaroori: TELEGRAM_BOT_TOKEN aur TELEGRAM_CHAT_ID environment variables
(GitHub Secrets) se aate hain - code mein hardcode NAHI kiye jate.
"""

import asyncio
import os
import time
import logging
import requests
from playwright.async_api import async_playwright

# ============ CONFIG ============
SEARCH_URL = "https://www.google.com/search?q=Charles+Plumbing+Services+Ltd"
BUSINESS_NAME_HINT = "Charles Plumbing Services Ltd"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# ==================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID missing hai (GitHub Secrets check karein).")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            logging.info("Telegram alert bheja gaya.")
        else:
            logging.error(f"Telegram alert fail: {r.status_code} - {r.text}")
    except Exception as e:
        logging.error(f"Telegram request error: {e}")


async def check_message_button(page) -> bool:
    """Business panel ke andar 'Message' button/link dhoondta hai (generic detection)."""
    try:
        candidates = await page.locator("text=/^Message$/").all()
        for c in candidates:
            if await c.is_visible():
                return True

        aria_candidates = await page.locator('[aria-label="Message"]').all()
        for c in aria_candidates:
            if await c.is_visible():
                return True

        return False
    except Exception as e:
        logging.error(f"Detection error: {e}")
        return False


async def run_check():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-GB",
        )
        page = await context.new_page()

        try:
            await page.goto(SEARCH_URL, timeout=20000)
            await page.wait_for_timeout(2000)

            body_text = await page.locator("body").inner_text()
            if BUSINESS_NAME_HINT not in body_text:
                logging.warning("Business panel is check mein nahi mila - page structure change ho sakta hai.")

            is_on = await check_message_button(page)

            if is_on:
                logging.info("MESSAGE BUTTON MILA - status: ON")
                send_telegram_alert(
                    f"🔔 ALERT: {BUSINESS_NAME_HINT} ke messages ON hain abhi!\n"
                    f"Waqt: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            else:
                logging.info("Message button nahi mila - status: OFF")

        except Exception as e:
            logging.error(f"Page load/check error: {e}")
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_check())
