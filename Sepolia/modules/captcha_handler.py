"""
CAPTCHA обробник з повторними спробами та вибором сервісу для hCaptcha/recaptcha
Користувач: Zasmin12ve
Дата: 2025-09-06
"""

import logging
import time
from captcha import CaptchaSolver
from config import CAPTCHA_CONFIG, TIMING

logger = logging.getLogger()

class CaptchaHandler:
    """CAPTCHA обробник з мінімальними логами та підтримкою повторних спроб"""

    def __init__(self, proxy: str):
        self.proxy = proxy
        self.max_attempts = CAPTCHA_CONFIG.get("max_captcha_attempts", 3)
        self.retry_delay = CAPTCHA_CONFIG.get("captcha_retry_delay_minutes", 2) * 60  # в секундах

    def solve_and_inject(self, page) -> bool:
        """Розв'язання CAPTCHA з повторними спробами і вибором сервісу"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                time.sleep(3)

                # --- Детекція типу капчі (залишаємо як було) ---
                captcha_info = self._detect_captcha(page)
                if not captcha_info:
                    logger.error("❌ Не визначено тип капчі")
                    return False

                captcha_type = captcha_info['type']
                solve_type = captcha_info['solve_type']

                # --- Вибір сервісу ---
                if captcha_type == 'hcaptcha':
                    solver_service = CAPTCHA_CONFIG.get("service_hcaptcha", "solvium")
                else:
                    solver_service = CAPTCHA_CONFIG.get("service_recaptcha", "2captcha")

                solver = CaptchaSolver(solver_service, self.proxy)

                logger.info(f"🔍 CAPTCHA: {captcha_type.upper()} | Спроба {attempt}/{self.max_attempts}")

                solution = solver.solve(solve_type)
                if not solution:
                    logger.error("❌ Розв'язання не вдалося")
                    raise Exception("No solution returned")

                logger.info(f"✅ Розв'язано за {int(time.time()) % 100}с")

                # --- Вставлення токена (залишаємо як було) ---
                success = self._inject_token(page, solution, captcha_type)
                if success:
                    time.sleep(5)
                    # --- Перевірка результату (залишаємо як було) ---
                    if self._check_result(page):
                        return True
                    else:
                        raise Exception("Token injected but mining not started")

                raise Exception("Token inject error")
            except Exception as e:
                logger.error(f"❌ CAPTCHA: {e}")
                if attempt < self.max_attempts:
                    logger.info(f"🔄 Затримка {self.retry_delay // 60} хвилин перед наступною спробою")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("❌ Досягнуто максимуму спроб")
                    return False
        return False

    def _detect_captcha(self, page) -> dict:
        """
        Тиха детекція (залишаємо як було)
        Повертає словник: {'type': ..., 'solve_type': ...}
        """
        try:
            for attempt in range(3):
                result = page.evaluate("""
                    () => {
                        // Швидка детекція hCaptcha
                        const hcaptchaIframes = document.querySelectorAll('iframe[src*="hcaptcha"]');
                        if (hcaptchaIframes.length > 0) {
                            return {type: 'hcaptcha', solve_type: 'sepolia_noname'};
                        }

                        // Швидка детекція reCaptcha
                        const recaptchaIframes = document.querySelectorAll('iframe[src*="recaptcha"]');
                        if (recaptchaIframes.length > 0) {
                            return {type: 'recaptcha', solve_type: 'sepolia_recaptcha'};
                        }

                        // API перевірка
                        if (window.hcaptcha) return {type: 'hcaptcha', solve_type: 'sepolia_noname'};
                        if (window.grecaptcha) return {type: 'recaptcha', solve_type: 'sepolia_recaptcha'};

                        return null;
                    }
                """)

                if result:
                    return result
                time.sleep(1)
            return None
        except Exception:
            return None

    def _inject_token(self, page, solution: str, captcha_type: str) -> bool:
        """
        Вставлення токена (залишаємо як було)
        """
        try:
            escaped_token = solution.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")

            if captcha_type == 'hcaptcha':
                result = page.evaluate(f"""
                    (() => {{
                        try {{
                            const token = "{escaped_token}";
                            document.querySelectorAll('textarea[name="h-captcha-response"]').forEach(el => el.remove());
                            const textarea = document.createElement('textarea');
                            textarea.name = 'h-captcha-response';
                            textarea.value = token;
                            textarea.style.cssText = 'position: absolute; left: -9999px; opacity: 0;';
                            document.body.appendChild(textarea);
                            if (window.hcaptcha) window.hcaptcha.getResponse = () => token;
                            window.captchaSolved = true;
                            setTimeout(() => textarea.dispatchEvent(new Event('change', {{bubbles: true}})), 100);
                            return true;
                        }} catch(e) {{ return false; }}
                    }})()
                """)
            else:  # recaptcha
                result = page.evaluate(f"""
                    (() => {{
                        try {{
                            const token = "{escaped_token}";
                            document.querySelectorAll('textarea[name="g-recaptcha-response"]').forEach(el => el.remove());
                            const textarea = document.createElement('textarea');
                            textarea.name = 'g-recaptcha-response';
                            textarea.value = token;
                            textarea.style.cssText = 'position: absolute; left: -9999px; opacity: 0;';
                            document.body.appendChild(textarea);
                            if (window.grecaptcha) window.grecaptcha.getResponse = () => token;
                            window.captchaSolved = true;
                            setTimeout(() => textarea.dispatchEvent(new Event('change', {{bubbles: true}})), 100);
                            return true;
                        }} catch(e) {{ return false; }}
                    }})()
                """)
            return result
        except Exception:
            return False

    def _check_result(self, page) -> bool:
        """
        Тиха перевірка (залишаємо як було)
        """
        try:
            for attempt in range(20):
                try:
                    mining_detected = page.evaluate("""
                        () => {
                            const text = document.body.textContent.toLowerCase();
                            const hasMining = ['h/s', 'hashrate', 'sepeth'].some(word => text.includes(word));
                            const isMiningUrl = window.location.pathname.includes('/mining/');
                            return hasMining || isMiningUrl;
                        }
                    """)
                    if mining_detected:
                        return True
                    time.sleep(1)
                except Exception:
                    time.sleep(1)
            return False
        except Exception:
            return False