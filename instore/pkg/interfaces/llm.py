from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

from langchain_core.tools import BaseTool


class LLM(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Sequence[BaseTool],
    ) -> tuple[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass
