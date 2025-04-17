import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from requests.models import HTTPError

from pkg.config import OCTOConfig
from pkg.interfaces.llm import LLM


class OCTOLLM(LLM):
    llm_config: OCTOConfig
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stop: Optional[List[str]] = None
    max_retries: int = 2
    tool_call_prefix: str = "[TOOL_CALL]"
    tool_call_suffix: str = "[/TOOL_CALL]"

    def __init__(
        self,
        llm_config: OCTOConfig,
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

    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, List[Dict[str, Any]]]:
        data = {
            "model": self.llm_config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        headers = {"Authorization": f"Bearer {os.environ.get('NT_BEARER_TOKEN')}"}

        try:
            response = requests.post(
                url=self.llm_config.endpoint,
                json=data,
                headers=headers,
                timeout=10000,
            )

            response.raise_for_status()

            reply = response.json()["choices"][0]["message"]

            reply["reasoning_content"] = ""
            content = reply["content"]
            tool_calls = reply["tool_calls"]

            return self.__extract_toolcall_from_content(content, tool_calls)

        except requests.exceptions.HTTPError as err:
            print(err)
            raise HTTPError() from err

    def get_model(self) -> str:
        return self.llm_config.model_name_pretty

    def __extract_toolcall_from_content(
        self, content: str, tool_calls: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict[str, Any]]]:
        if self.tool_call_prefix not in content:
            return content, tool_calls

        without_prefix = content.split(self.tool_call_prefix, 1)[-1]
        tool_call = without_prefix.split(self.tool_call_suffix, 1)[0]
        parsed_content = json.loads(tool_call)
        parsed_content["id"] = str(uuid4())
        tool_calls.append(parsed_content)

        return "", tool_calls
