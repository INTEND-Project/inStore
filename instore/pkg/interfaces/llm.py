from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLM(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass
