import json
import os
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import requests
from langchain_core.messages.tool import tool_call
from langchain_core.tools import BaseTool
from requests.models import HTTPError
from transformers import AutoTokenizer
from vllm import LLM, sampling_params
from vllm.entrypoints.openai.protocol import ChatCompletionRequest

from pkg.config import VLLMConfig
from pkg.interfaces.llm import LLM
from pkg.llms.qwen3coder_tool_parser import Qwen3CoderToolParser


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
        if os.environ.get("VLLM_MODEL_NAME") is not None:
            model_name = os.environ.get("VLLM_MODEL_NAME")
        if os.environ.get("VLLM_ENDPOINT") is not None:
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

            content = reply["content"]
            tool_calls = []
            tcs = reply["tool_calls"]
            if tcs is not None:
                for tc in tcs:
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
        except Exception as err:
            print(err)
            return err, []

    def get_model(self) -> str:
        return self.llm_config.model_name_pretty
