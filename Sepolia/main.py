"""
Sepolia Faucet Automator - компактні логи + новий браузер кожен цикл
Користувач: Zasmin12ve
Дата: 2025-09-09 12:31:26 UTC
"""

import logging
import sys
import time
from playwright.sync_api import sync_playwright

# Компактне налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('mining.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Імпорти модулів
from config import *
from modules.captcha_handler import CaptchaHandler
from modules.mining import MiningController
from modules.browser import BrowserSession

logger = logging.getLogger()


def process_mining_cycle(page, wallet: str, captcha: CaptchaHandler, mining: MiningController) -> bool:
    """Цикл майнінгу з мінімальними логами"""

    try:
        # Перевіряємо чи вже на сторінці майнінгу
        current_url = page.url
        if '/mining/' in current_url:
            logger.info("⏩ Вже на майнінгу, переходжу до моніторингу")
            mining.monitor(page)
            mining.claim(page)
            return True

        # 1. Введення адреси
        try:
            wallet_input = page.wait_for_selector(SELECTORS['wallet'], timeout=60000)
            wallet_input.fill("")
            wallet_input.fill(wallet)
            logger.info(f"📝 Адреса введена: {wallet[:10]}...{wallet[-6:]}")
        except Exception as e:
            logger.error(f"❌ Помилка адреси: {e}")
            return False

        # 2. CAPTCHA (тихо)
        if not captcha.solve_and_inject(page):
            logger.error("❌ CAPTCHA не розв'язано")
            return False

        time.sleep(2)

        # 3. Запуск майнінгу
        if not mining.start(page):
            logger.error("❌ Майнінг не запущено")
            return False

        # 4. Моніторинг
        mining.monitor(page)

        # 5. Клейм
        if not mining.claim(page):
            logger.error("❌ Помилка клейму")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Помилка: {e}")
        return False


def load_data():
    """Завантаження даних"""
    try:
        with open('wallets.txt', 'r', encoding='utf-8') as f:
            wallets = [line.strip() for line in f.readlines() if line.strip()]
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f.readlines() if line.strip()]
        return wallets, proxies
    except Exception as e:
        logger.error(f"❌ Помилка файлів: {e}")
        sys.exit(1)


def process_wallet(wallet: str, proxy: str, index: int) -> bool:
    """Обробка одного гаманця - НОВИЙ БРАУЗЕР КОЖЕН ЦИКЛ"""
    wallet_short = f"{wallet[:6]}...{wallet[-4:]}"
    proxy_short = proxy.split(':')[0] if ':' in proxy else proxy[:15]

    logger.info(f"🚀 СТАРТ: {wallet_short} | Proxy: {proxy_short}")

    try:
        with sync_playwright() as p:
            # Цикли з НОВИМ браузером кожен раз
            for cycle in range(CYCLES):
                logger.info(f"🔄 Цикл {cycle + 1}/{CYCLES} - НОВИЙ БРАУЗЕР")
                
                # === НОВИЙ БРАУЗЕР КОЖЕН ЦИКЛ ===
                with BrowserSession(proxy, f"{index}_{cycle}") as session:
                    if not session.start(p):
                        logger.error(f"❌ Браузер цикл {cycle + 1} не запустився")
                        continue

                    # Ініціалізація для цього циклу
                    captcha = CaptchaHandler(session.proxy_data['url'])
                    mining = MiningController()

                    page = session.get_page()
                    if not page:
                        logger.error(f"❌ Сторінка цикл {cycle + 1} не завантажилась")
                        continue

                    try:
                        # Навігація
                        page.goto("https://sepolia-faucet.pk910.de/", timeout=90000, wait_until='networkidle')

                        # Процес майнінгу
                        success = process_mining_cycle(page, wallet, captcha, mining)
                        if success:
                            logger.info(f"✅ Цикл {cycle + 1} завершено успішно")
                        else:
                            logger.error(f"❌ Цикл {cycle + 1} провалено")

                    except Exception as cycle_error:
                        logger.error(f"❌ Цикл {cycle + 1}: {cycle_error}")
                    finally:
                        if page and not page.is_closed():
                            page.close()
                        logger.info(f"🔄 Браузер цикл {cycle + 1} закрито")

                # Пауза між циклами (опціонально)
                if cycle < CYCLES - 1:
                    logger.info("⏸️ Пауза між циклами: 30с")
                    time.sleep(30)

        logger.info(f"✅ ЗАВЕРШЕНО: {wallet_short}")
        return True

    except Exception as e:
        logger.error(f"❌ КРИТИЧНА: {wallet_short} - {e}")
        return False


def main():
    """Головна функція"""
    logger.info("🚀 Sepolia Automator - НОВИЙ БРАУЗЕР КОЖЕН ЦИКЛ")
    logger.info(f"👤 {USER} | 🎯 {TARGET_AMOUNT} ETH | 🔄 {CYCLES} циклів")
    logger.info("=" * 60)

    try:
        wallets, proxies = load_data()

        for i, (wallet, proxy) in enumerate(zip(wallets, proxies)):
            try:
                process_wallet(wallet, proxy, i)
                logger.info("-" * 40)
            except Exception as e:
                logger.error(f"❌ Помилка: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("⏹️ ЗУПИНЕНО")
    except Exception as e:
        logger.error(f"💥 КРИТИЧНА: {e}")
    finally:
        logger.info("🏁 ЗАВЕРШЕНО")


if __name__ == "__main__":
    main()
