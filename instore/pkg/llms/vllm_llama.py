import json
import os
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

import requests
from langchain_core.messages import ToolMessage
from langchain_core.messages.tool import tool_call
from langchain_core.tools import BaseTool
from requests.models import HTTPError

from pkg.config import VLLMConfig
from pkg.interfaces.llm import LLM


class VLLM_LLAMA(LLM):
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

        system_prompt = (
            system_prompt
            + f"""
        Available Tools:{[
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {"type": "object", "properties": t.args},
            },
        }
        for t in tools
    ],}"""
        )
        system_prompt = (
            system_prompt
            + 'If using a tool, respond as follows, only call one tool at a time, and make sure that it is a valid json: <tool_call>{"type": "function", "function": {"name": "IntentConflictDetector", "arguments": {"start_date": "2025-09-01", "end_date": "2025-09-30", "objective": "reduce_cost"}"}}</tool_call> '
        )
        data = {
            "model": model_name,
            "temperature": 0.4,
            # "chat_template_kwargs": {"enable_thinking": False},
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

            tool_calls = []

            tool_calls_str = ""
            # Hack because LLMs being LLMs, nightmare parsing ahead that needs to be cleaned up
            parts = reply["content"].split("<tool_call>")
            if len(parts) > 1:
                tool_calls_str = parts[1].split("</tool_call>")[0]
            elif len(reply["content"].split('{"type": "function"')) > 1:
                tool_calls_str = '{"type":' + reply["content"].split('{"type":', 1)[-1]
                if tool_calls_str.count("{") < tool_calls_str.count("}"):
                    print("Removing: " + tool_calls_str)
                    tool_calls_str = tool_calls_str[: len(tool_calls_str) - 1]
                if tool_calls_str.count("{") > tool_calls_str.count("}"):
                    print("Adding: " + tool_calls_str)
                    tool_calls_str = tool_calls_str + "}"
            else:  # No tool calls
                return reply["content"], tool_calls
            tool_calls_str = tool_calls_str.replace("\\'", "'")
            if "IntentDatabase" not in tool_calls_str:
                tool_calls_str = tool_calls_str.replace("'", '"')

            print(tool_calls_str)
            tool_calls_str = tool_calls_str.replace('\\"', '"')
            tool_calls_str = tool_calls_str.replace('"[', "[")
            tool_calls_str = tool_calls_str.replace(']"', "]")
            tool_calls_str = tool_calls_str.replace('"{', "{")
            tool_calls_str = tool_calls_str.replace('}"', "}")
            print(tool_calls_str)
            tc = json.loads(tool_calls_str)

            if "function" in tc:

                tool_calls.append(
                    {
                        "name": tc["function"]["name"],
                        "args": (
                            tc["function"]["arguments"]
                            if "arguments" in tc["function"]
                            else tc["function"]["parameters"]
                        ),
                        "id": str(uuid4()),
                    }
                )
            elif "name" in tc:
                print(tc)
                tool_calls.append(
                    {
                        "name": tc["name"],
                        "args": tc["arguments"] if "arguments" in tc else tc["parameters"],
                        "id": str(uuid4()),
                    }
                )
            return reply["content"], tool_calls

        except requests.exceptions.HTTPError as err:

            print(err)
            raise HTTPError() from err
        except json.decoder.JSONDecodeError as err:
            print(err)
            return (
                f"error: Message from tool: bad input given to a tool which caused the following error: {err}",
                [],
            )

    def get_model(self) -> str:
        return self.llm_config.model_name_pretty
