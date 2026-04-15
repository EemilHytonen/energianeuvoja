from abc import ABC, abstractmethod
import requests
from modules.logger import get_logger

logger = get_logger("LLMInterface")

class LLMInterface(ABC):
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        pass

class DeepSeekLLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        logger.info(f"DeepSeekLLM alustettu")

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature}
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                error_msg = f"API-virhe {response.status_code}"
                logger.error(error_msg)
                return error_msg
        except Exception as e:
            logger.exception(f"Poikkeus API-kutsussa: {e}")
            return f"Virhe: {e}"