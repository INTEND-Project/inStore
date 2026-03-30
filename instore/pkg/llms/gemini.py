import os
from typing import Any, Dict, List, Sequence
from uuid import uuid4

import requests
from google import genai
from google.genai import types
from langchain_core.tools import BaseTool
from requests.models import HTTPError

from pkg.config.llms import GeminiConfig
from pkg.interfaces.llm import LLM


class GeminiLLM(LLM):
    llm_config: GeminiConfig

    def __init__(self, llm_config: GeminiConfig):
        self.llm_config = llm_config

    def generate(
        self, system_prompt: str, user_prompt: str, tools: Sequence[BaseTool]
    ) -> tuple[str, List[Dict[str, Any]]]:
        api_key = os.environ.get("GEMINI_API_KEY")
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "tools": [{"functionDeclarations": self._parameters_from_tools(tools)}],
        }

        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
        try:
            response = requests.post(
                url=self.llm_config.endpoint,
                json=data,
                headers=headers,
                timeout=60,
            )
            print("done")

            response.raise_for_status()

            reply = response.json()["candidates"][0]

            content: str = ""
            tool_calls: list[dict[str, Any]] = []
            if "content" not in reply:
                print(data)
                print(f"\n\n\n{reply}\n\n\n")
            parts: list[dict[str, Any]] = reply["content"]["parts"]
            for part in parts:
                if list(part.keys())[0] == "functionCall":
                    part["functionCall"]["id"] = str(uuid4())
                    tool_calls.append(part["functionCall"])
                if list(part.keys())[0] == "text":
                    content = part["text"]

            return content, tool_calls

        except requests.exceptions.HTTPError as err:
            print(err)
            raise HTTPError() from err

    def get_model(self) -> str:
        return self.llm_config.model_name_pretty

    def _parameters_from_tools(self, tools: Sequence[BaseTool]):
        function_declarations = []
        for tool in tools:
            gemini_tool = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.args,
                    "required": [name for name in tool.args],
                },
            }
            function_declarations.append(gemini_tool)
        return function_declarations
