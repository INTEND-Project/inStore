import json
import os
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import requests
from langchain_core.tools import BaseTool
from requests.models import HTTPError

from pkg.config import VLLMConfig
from pkg.interfaces.llm import LLM


class VLLM(LLM):
    llm_config: VLLMConfig
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stop: Optional[List[str]] = None
    max_retries: int = 2

    def __init__(
        self,
        llm_config: VLLMConfig,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        max_retries: int = 2,
    ):
        self.llm_config = llm_config
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stop = stop
        self.max_retries = max_retries

    def generate(
        self, system_prompt: str, user_prompt: str, tools: Sequence[BaseTool]
    ) -> tuple[str, List[Dict[str, Any]]]:
        model_name = self.llm_config.model_name
        vllm_url = self.llm_config.endpoint
        data = {
            "model": model_name,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": {"type": "object", "properties": t.args},
                    },
                }
                for t in tools
            ],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {os.environ.get('NT_BEARER_TOKEN')}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url=vllm_url,
                json=data,
                headers=headers,
                timeout=10000,
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]

            # Some vLLM servers omit tool_calls when no tool is called, and send null content alongside tool calls
            content = reply.get("content") or ""
            tool_calls = []
            for tc in reply.get("tool_calls") or []:
                tool_calls.append(
                    {
                        "name": tc["function"]["name"],
                        "args": json.loads(tc["function"]["arguments"]),
                        "id": tc["id"],
                    }
                )
            print(reply)
            return (
                content,
                tool_calls,
            )

        except requests.exceptions.HTTPError as err:
            print(err)
            raise HTTPError() from err

    def get_model(self) -> str:
        return self.llm_config.model_name_pretty
