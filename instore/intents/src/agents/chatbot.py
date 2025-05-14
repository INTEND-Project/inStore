import os
from typing import Any, Dict, List, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from pkg.interfaces import LLM

NT_BEARER_TOKEN = os.environ.get("NT_BEARER_TOKEN")


class Chatbot(BaseChatModel):

    llm: LLM
    tool_call_prefix: str = "[TOOL_CALL]"
    tool_call_suffix: str = "[/TOOL_CALL]"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:

        user_prompt: str = str(messages[-1].content)
        system_prompt = """You are a helpful assistant for a storage management tool. Users
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
                """

        content, tool_calls = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )
        msg = AIMessage(content=content, tool_calls=tool_calls)
        generation = ChatGeneration(message=msg)
        return ChatResult(generations=[generation])

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.llm.get_model()}

    @property
    def _llm_type(self) -> str:
        return "custom"
