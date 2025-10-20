"""
Браузер менеджер
"""
import logging
import os
import shutil
from playwright.sync_api import sync_playwright
from fake_useragent import UserAgent
from config import CAPTCHA_CONFIG, SELECTORS

logger = logging.getLogger()


class BrowserSession:
    """Сесія браузера"""

    def __init__(self, proxy_str: str, profile_id: int):
        self.proxy_data = self._parse_proxy(proxy_str)
        self.profile_dir = f"profile_{profile_id}"
        self.context = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def start(self, playwright):
        """Запуск браузера"""
        try:
            self.context = playwright.chromium.launch_persistent_context(
                self.profile_dir,
                headless=False,
                proxy={
                    "server": f"http://{self.proxy_data['host']}:{self.proxy_data['port']}",
                    "username": self.proxy_data['user'],
                    "password": self.proxy_data['pass']
                },
                user_agent=UserAgent().random,
                viewport={'width': 1280, 'height': 720}
            )
            return True
        except Exception as e:
            logger.error(f"Помилка запуску браузера: {e}")
            return False

    def get_page(self):
        """Отримання сторінки"""
        try:
            page = self.context.pages[0] if self.context.pages else self.context.new_page()
            page.goto(CAPTCHA_CONFIG["url"], timeout=90000, wait_until='networkidle')
            return page
        except Exception as e:
            logger.error(f"Помилка сторінки: {e}")
            return None

    def enter_wallet(self, page, wallet: str) -> bool:
        """Введення адреси гаманця"""
        try:
            input_field = page.wait_for_selector(SELECTORS['wallet'], timeout=30000)
            input_field.fill("")
            input_field.fill(wallet)
            logger.info(f"✅ Введено: {wallet}")
            return True
        except Exception as e:
            logger.error(f"Помилка введення: {e}")
            return False

    def cleanup(self):
        """Очищення"""
        try:
            if self.context:
                self.context.close()
            if os.path.exists(self.profile_dir):
                shutil.rmtree(self.profile_dir, ignore_errors=True)
        except:
            pass

    def _parse_proxy(self, proxy_str: str) -> dict:
        """Парсинг проксі"""
        parts = proxy_str.split(':')
        return {
            'host': parts[0], 'port': parts[1],
            'user': parts[2], 'pass': parts[3],
            'url': f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        }