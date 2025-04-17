import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from requests.exceptions import HTTPError

NT_BEARER_TOKEN = os.environ.get("NT_BEARER_TOKEN")


class Chatbot(BaseChatModel):

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stop: Optional[List[str]] = None
    max_retries: int = 2
    tool_call_prefix: str = "[TOOL_CALL]"
    tool_call_suffix: str = "[/TOOL_CALL]"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:

        prompt = messages[-1].content
        url = "http://10.60.26.10/api/chat/completions"
        data = {
            "model": "qwen/qwq-32b",
            "messages": [
                {
                    "role": "system",
                    "content": """You are a helpful assistant for a storage management tool. Users
                                will ask you to manage the placement of data.


                                If you can answer without a tool, just provide the final answer. 
                                Otherwise, here are the list of tools you can call if it is 
                                relevant to the user's question. 
                                [
                                    {
                                        'name': 'DataPlacementOptimizer', 
                                        'args': {
                                            'content_tag': 'a string describing a content category', 
                                            'action': 'one of the following values: ["reduce_cost", "reduce_latency", "balance_cost_and_latency"]')
                                        },

                                    }
                                ]

                                If you need to use a tool, respond in this format:
                                [TOOL_CALl]
                                {
                                    "name": <tool_name>, 
                                    "args": <args>

                                }
                                [/TOOL_CALL]

                                If you receive a prefix of [DataPlacementOptimizer], then that is 
                                the response of that specific tool. Convey the result of the tool 
                                to the user consicely and clearly.
                        """,
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        headers = {"Authorization": f"Bearer {os.environ.get('NT_BEARER_TOKEN')}"}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10000)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]
            reply["reasoning_content"] = ""

            content = reply["content"]
            tool_calls = reply["tool_calls"]

            content, tool_calls = self.__extract_toolcall_from_content(content, tool_calls)

            msg = AIMessage(content=[content], additional_kwargs={}, tool_calls=tool_calls)
            generation = ChatGeneration(message=msg)
            return ChatResult(generations=[generation])
        except requests.exceptions.HTTPError as err:
            print(err)
            raise HTTPError() from err

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "qwen/qwq-32b"}

    @property
    def _llm_type(self) -> str:
        return "custom"

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
