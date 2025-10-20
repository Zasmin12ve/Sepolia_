"""
Mining контролер - з прогрес-баром
Користувач: Zasmin12ve
Дата: 2025-08-15 07:32:51 UTC
"""
import logging
import time
import re
import sys
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config import LOCATORS, TIMING, TARGET_AMOUNT

logger = logging.getLogger()

class MiningController:
    """Mining з прогрес-баром"""

    def __init__(self):
        self.farmed_amount_locator = LOCATORS['farmed_amount']
        self.claimed_amount_locator = LOCATORS['claimed_amount']
        self.target_amount = TARGET_AMOUNT
        self.wait_time_seconds = TIMING['wait_time_seconds']
        self.check_interval = TIMING['check_interval']

    def start(self, page) -> bool:
        """Запуск майнінгу"""
        try:
            start_button = page.locator('//button[contains(text(), "Start Mining")]')
            if start_button.is_visible(timeout=5000):
                start_button.click()
                logger.info("⚡ Start Mining")
                time.sleep(TIMING['after_start_delay'])
            else:
                return False

            try:
                page.wait_for_selector(self.farmed_amount_locator, timeout=10000)
                logger.info("✅ Майнінг запущено")
                return True

            except PlaywrightTimeoutError:
                close_button = page.locator('//div[contains(@class, "modal-content")]//button[contains(text(), "Close")]')
                if close_button.is_visible(timeout=5000):
                    close_button.click()
                    time.sleep(2)
                return False

        except Exception:
            return False

    def _create_progress_bar(self, current, target, width=20):
        """Створює прогрес-бар"""
        if target == 0:
            percentage = 0
        else:
            percentage = min(current / target, 1.0)

        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage*100:.1f}%"

    def monitor(self, page):
        """Моніторинг з прогрес-баром"""
        try:
            logger.info(f"⏳ Моніторинг до {self.target_amount} ETH...")
            start_time = time.time()
            last_amount = 0

            while True:
                elapsed_time = time.time() - start_time

                if elapsed_time >= self.wait_time_seconds:
                    print()
                    logger.info("⏰ Таймаут досягнуто")
                    break

                try:
                    amount_element = page.locator(self.farmed_amount_locator).first
                    current_amount_text = amount_element.inner_text()

                    match = re.search(r'[\d.]+', current_amount_text.replace(',', '.'))
                    if match:
                        current_amount = float(match.group(0))

                        # Оновлюємо якщо сума змінилась або кожні 30 секунд
                        if current_amount != last_amount or int(elapsed_time) % 30 == 0:
                            remaining = self.wait_time_seconds - elapsed_time
                            h, m = divmod(remaining, 3600)
                            m = int(m / 60)

                            # Прогрес-бар
                            progress_bar = self._create_progress_bar(current_amount, self.target_amount)

                            # Динамічний рядок
                            progress_text = f"💰 {current_amount:.4f}/{self.target_amount} ETH {progress_bar} | ⏰ {int(h)}h{m}m"
                            print(f"\r{progress_text}", end='', flush=True)

                            last_amount = current_amount

                        if current_amount >= self.target_amount:
                            print()
                            logger.info("🎯 ЦІЛЬ ДОСЯГНУТО!")
                            break

                except Exception:
                    pass

                time.sleep(self.check_interval)

        except Exception as e:
            print()
            logger.error(f"❌ Моніторинг: {e}")

    def claim(self, page):
        """Компактний клейм"""
        try:
            # Stop Mining & Claim
            stop_claim_button = page.locator('//button[contains(text(), "Stop Mining & Claim Rewards")]')
            if stop_claim_button.is_visible(timeout=10000):
                stop_claim_button.click()
                logger.info("🛑 Stop Mining")
                time.sleep(TIMING['after_stop_delay'])
            else:
                return False

            # Claim Rewards
            claim_button = page.locator('//button[contains(text(), "Claim Rewards")]')
            if claim_button.is_visible(timeout=10000):
                claim_button.click()
                logger.info("💎 Claim Rewards")
                time.sleep(TIMING['after_claim_delay'])
            else:
                return False

            # Результат
            try:
                amount_element = page.locator(self.claimed_amount_locator).first
                amount_text = amount_element.inner_text()

                logger.info("="*50)
                logger.info(f"🏆 ЗАКЛЕЙМЛЕНО: {amount_text}")
                logger.info("="*50)

            except Exception as e:
                logger.warning(f"⚠️ Не вдалося прочитати суму: {e}")

            time.sleep(5)
            return True

        except Exception as e:
            logger.error(f"❌ Клейм: {e}")
            return False

    def return_to_start(self, page):
        """Тихе повернення"""
        try:
            return_button = page.locator('//button[contains(text(), "Return to startpage")]')
            if return_button.is_visible(timeout=10000):
                return_button.click()
                time.sleep(5)
                return True
            else:
                page.reload()
                time.sleep(10)
                return True

        except Exception:
            return False