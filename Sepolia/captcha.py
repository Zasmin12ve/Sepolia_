from time import sleep
import logging
from requests import request

# Змінюємо імпорти на абсолютні
try:
    from settings import SOLVIUM_KEY
except ImportError:
    SOLVIUM_KEY = "Z0AGIJkNHQG55BLEpihJsaApVZzc41t8"  # Замініть на ваш повний ключ
    CAPTCHA_KEY_2CAPTCHA = "dd9a30e28506247a2d72aecf446bbc24"

try:
    from config import captcha_ids
except ImportError:
    captcha_ids = {
        "solvium": {
            "param": "ref",
            "id": ""
        }
    }

# Налаштування логування
logger = logging.getLogger(__name__)


class CaptchaSolver:
    captcha_services: dict = {
        "2captcha": {"url": "api.2captcha.com", "type": "standard"},
        "capmonster": {"url": "api.capmonster.cloud", "type": "standard"},
        "capsolver": {"url": "api.capsolver.com", "type": "standard"},
        "anticaptcha": {"url": "api.anti-captcha.com", "type": "standard"},
        "solvium": {"url": "captcha.solvium.io/api/v1/task", "type": "solvium"},
    }

    def __init__(self, captcha_service: str, proxy: str | None):
        if proxy:
            self.proxy = {"http": proxy, "https": proxy}
        else:
            self.proxy = None

        if captcha_service.lower() not in self.captcha_services:
            raise Exception(f'Not supported captcha service: `{captcha_service}`')

        self.captcha_service_name = captcha_service.lower()
        self.captcha_service = self.captcha_services[captcha_service.lower()]

    def solve(self, captcha_type: str, **kwargs):
        # --- NEW: reCaptcha через 2Captcha ---
        if self.captcha_service_name == "2captcha" and captcha_type in ["sepolia_recaptcha", "recaptcha_custom"]:
            params = {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": kwargs.get("websiteURL", "https://sepolia-faucet.pk910.de"),
                "websiteKey": kwargs.get("websiteKey", "6Leg_psiAAAAAHlE_PSnJuYLQDXbrnBw6G2l_vvu"),
                # додаткові параметри можна додати тут
            }
        # --- залишаємо інші як було ---
        elif captcha_type == "camp_faucet":
            params = {
                "solvium_type": "noname",
                "websiteURL": "https://faucet.campnetwork.xyz/",
                "websiteKey": "5b86452e-488a-4f62-bd32-a332445e2f51",
                "method": "GET",
            }

        elif captcha_type == "camp_loyalty":
            params = {
                "solvium_type": "cf-clearance",
                "websiteURL": "https://loyalty.campnetwork.xyz/loyalty/",
                "body": kwargs["body"],
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "POST",
            }

        elif captcha_type == "cf_scoreplay":
            params = {
                "solvium_type": "cf-clearance",
                "websiteURL": "https://app.scoreplay.xyz/rewards",
                "body": kwargs["body"],
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "POST",
            }

        elif captcha_type == "scoreplay":
            params = {
                "type": "TurnstileTaskProxyless",
                "solvium_type": "turnstile",
                "websiteURL": "https://app.scoreplay.xyz/",
                "websiteKey": "0x4AAAAAABgcc9z2p-IJlyu-",
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "GET",
            }

        # NONAME CAPTCHA для Sepolia (hCaptcha-подібна)
        elif captcha_type == "sepolia_noname":
            params = {
                "solvium_type": "noname",
                "websiteURL": "https://sepolia-faucet.pk910.de",
                "websiteKey": "89693841-2505-4039-8c39-479c9188991f",
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "GET",
            }

        # reCAPTCHA для Sepolia через solvium (залишаємо для сумісності)
        elif captcha_type == "sepolia_recaptcha" and self.captcha_service_name != "2captcha":
            params = {
                "solvium_type": "recaptcha-v2",
                "websiteURL": "https://sepolia-faucet.pk910.de",
                "websiteKey": "6Leg_psiAAAAAHlE_PSnJuYLQDXbrnBw6G2l_vvu",
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "GET",
            }

        # Автоматичне визначення для Sepolia (залишаємо для сумісності)
        elif captcha_type == "sepolia_faucet":
            params = {
                "solvium_type": "noname",
                "websiteURL": "https://sepolia-faucet.pk910.de",
                "websiteKey": "89693841-2505-4039-8c39-479c9188991f",
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "GET",
            }

        # Універсальний варіант для динамічних параметрів
        elif captcha_type == "recaptcha_custom" and self.captcha_service_name != "2captcha":
            params = {
                "solvium_type": "recaptcha-v2",
                "websiteURL": kwargs.get("websiteURL", "https://sepolia-faucet.pk910.de"),
                "websiteKey": kwargs.get("websiteKey", "6Leg_psiAAAAAHlE_PSnJuYLQDXbrnBw6G2l_vvu"),
                "proxy": self.proxy["http"] if self.proxy else None,
                "method": "GET",
            }

        else:
            params = {}

        if captcha_ids.get(self.captcha_service_name):
            captcha_data = captcha_ids[self.captcha_service_name]
            params[captcha_data["param"]] = captcha_data["id"]

        task_id = self.request_solving(params=params)
        logger.info(f'[•] {captcha_type.replace("_", " ").title()} | Waiting for solve captcha #{task_id}')
        return self.get_result(task_id)

    def request_solving(self, params: dict):
        # --- 2Captcha (RecaptchaV2TaskProxyless) ---
        if self.captcha_service_name == "2captcha":
            r = request(
                method="POST",
                url=f"https://{self.captcha_service['url']}/createTask",
                json={
                    "clientKey": CAPTCHA_KEY_2CAPTCHA,
                    "task": params
                },
                proxies=self.proxy
            )
            logger.info(f"2Captcha response: {r.status_code} - {r.text}")
            if r.json().get("taskId") is None:
                raise Exception(f'Create captcha error: {r.json()}')
            return r.json()["taskId"]

        # --- стандартні/solvium сервіси ---
        r_method = params.pop("method").upper() if "method" in params else "POST"
        if self.captcha_service["type"] == "standard":
            r = request(
                method=r_method,
                url=f"https://{self.captcha_service['url']}/createTask",
                json={
                    "clientKey": "DEV_CAPTCHA_KEY",
                    "task": params
                },
                proxies=self.proxy
            )
            if r.json().get("taskId") is None:
                raise Exception(f'Create captcha error: {r.json()}')
            return r.json()["taskId"]

        elif self.captcha_service["type"] == "solvium":
            captcha_params = {
                v: params[k]
                for k, v in
                [["websiteURL", "url"], ["websiteKey", "sitekey"], ["body", "body"], ["proxy", "proxy"], ["ref", "ref"]]
                if params.get(k)}

            if r_method == "GET":
                request_params = captcha_params
                request_json = None
            elif r_method == "POST":
                request_params = None
                request_json = captcha_params

            r = request(
                method=r_method,
                url=f"https://{self.captcha_service['url']}/{params['solvium_type']}",
                params=request_params,
                json=request_json,
                headers={"authorization": "Bearer " + SOLVIUM_KEY},
                proxies=self.proxy
            )
            print(f"Solvium response: {r.status_code} - {r.text}")

            if r.json().get("task_id") is None:
                raise Exception(f'Create captcha error: {r.text}')
            return r.json()["task_id"]

    def get_result(self, task_id: int):
        for attempt in range(42):
            # --- 2Captcha ---
            if self.captcha_service_name == "2captcha":
                r = request(
                    method="POST",
                    url=f"https://{self.captcha_service['url']}/getTaskResult",
                    json={
                        "clientKey": CAPTCHA_KEY_2CAPTCHA,
                        "taskId": task_id
                    },
                    proxies=self.proxy
                )
                if r.json().get("errorId") != 0:
                    error_text = r.json().get("errorDescription") or r.json()
                    raise Exception(f'Solve captcha error: {error_text}')
                elif r.json().get("status") == "ready":
                    solution = r.json()["solution"]
                    # Для рекапчі це поле: gRecaptchaResponse
                    return solution.get("gRecaptchaResponse") or solution.get("token") or solution

            # --- стандарт/solvium ---
            elif self.captcha_service["type"] == "standard":
                r = request(
                    method="POST",
                    url=f"https://{self.captcha_service['url']}/getTaskResult",
                    json={
                        "clientKey": "DEV_CAPTCHA_KEY",
                        "taskId": task_id
                    },
                    proxies=self.proxy
                )
                if r.json().get("errorId") != 0:
                    error_text = r.json().get("errorDescription") or r.json()
                    raise Exception(f'Solve captcha error: {error_text}')
                elif r.json().get("status") == "ready":
                    solution = r.json()["solution"]
                    return solution.get("gRecaptchaResponse") or solution.get("token") or solution

            elif self.captcha_service["type"] == "solvium":
                r = request(
                    method="GET",
                    url=f"https://{self.captcha_service['url']}/status/{task_id}",
                    params={"task_id": task_id},
                    headers={"authorization": "Bearer " + SOLVIUM_KEY},
                    proxies=self.proxy
                )
                if r.json().get("status") == "completed":
                    solution = r.json()["result"]["solution"]
                    logger.info(f"✅ CAPTCHA solved: {solution[:50]}...")
                    return solution
                elif r.json().get("status") not in ["pending", "running"]:
                    error_text = r.json()
                    raise Exception(f'Solve captcha error: {error_text}')

            sleep(5)

        raise Exception(f'Captcha expired after {42 * 5} seconds')