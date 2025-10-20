"""
Конфігурація адаптована під твій скрипт
Користувач: Zasmin12ve
Дата: 2025-08-15 00:23:07 UTC
"""

# === ОСНОВНІ НАЛАШТУВАННЯ (з твого скрипта) ===
CYCLES = 2  # NUMBER_OF_CYCLES
ATTEMPTS = 1  # MAX_MINING_ATTEMPTS
TARGET_AMOUNT = 2.24  # з твого скрипта
WAIT_HOURS = 11  # WAIT_TIME_SECONDS / 3600

# === CAPTCHA КОНФІГУРАЦІЯ ===
CAPTCHA_CONFIG = {
    "service_hcaptcha": "solvium",      # hCaptcha тільки через solvium
    "service_recaptcha": "2captcha",    # reCaptcha тільки через 2captcha
    "url": "https://sepolia-faucet.pk910.de",
    "recaptcha_sitekey": "6Leg_psiAAAAAHlE_PSnJuYLQDXbrnBw6G2l_vvu",
    "hcaptcha_sitekey": "89693841-2505-4039-8c39-479c9188991f",
    "max_captcha_attempts": 5,
    "captcha_retry_delay_minutes": 2
}

# === СЕЛЕКТОРИ (з твого скрипта) ===
SELECTORS = {
    'wallet': 'input[placeholder="Please enter ETH address or ENS name"]',
    'start': '//button[contains(text(), "Start Mining")]',
    'stop_claim': '//button[contains(text(), "Stop Mining & Claim Rewards")]',
    'claim': '//button[contains(text(), "Claim Rewards")]',
    'return': '//button[contains(text(), "Return to startpage")]',
    'close_modal': '//div[contains(@class, "modal-content")]//button[contains(text(), "Close")]'
}

# === ЛОКАТОРИ СТАТИСТИКИ (з твого скрипта) ===
LOCATORS = {
    'farmed_amount': 'body > div.faucet-wrapper > div > div > div > div.faucet-body > div > div.pow-status-container > div > div.row.pow-status-top > div:nth-child(1) > div.status-value',
    'claimed_amount': 'body > div.faucet-wrapper > div > div > div > div.faucet-body > div > div > div:nth-child(2) > div:nth-child(2) > div.col'
}

# === ТАЙМІНГИ (з твого скрипта) ===
TIMING = {
    'wait_time_seconds': 36600,  # WAIT_TIME_SECONDS
    'check_interval': 10,  # CHECK_INTERVAL_SECONDS
    'captcha_timeout_minutes': 420,  # з твого скрипта
    'after_start_delay': 8,
    'after_stop_delay': 6,
    'after_claim_delay': 15
}

# === ВЕРСІЯ ===
VERSION = "ADAPTED FROM YOUR SCRIPT"
USER = "Zasmin12ve"
DATE = "2025-08-15 00:23:07 UTC"