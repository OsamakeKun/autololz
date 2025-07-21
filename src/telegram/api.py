import requests
from typing import Optional, Dict, Any


class TelegramAPI:
    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"{self.BASE_URL}{self.bot_token}"

    def api_request(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        http_method: str = "GET",
    ) -> Dict[str, Any]:
        url = f"{self.api_url}/{method}"
        if http_method.upper() == "GET":
            response = requests.get(url, params=data)
        else:
            response = requests.post(url, json=data)
        response.raise_for_status()  # выбросит исключение при ошибке HTTP
        return response.json()

    def send_message(
        self, text: str, chat_id: int, **kwargs
    ) -> Dict[str, Any]:
        payload = {"chat_id": chat_id, "text": text, **kwargs}
        return self.api_request("sendMessage", data=payload, http_method="POST")
