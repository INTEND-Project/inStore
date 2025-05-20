import os
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from pkg.interfaces import LLM

NT_BEARER_TOKEN = os.environ.get("NT_BEARER_TOKEN")


class Chatbot(BaseChatModel):

    llm: LLM
    tools: Sequence[BaseTool]

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        user_prompt: str = str(messages)
        system_prompt = """You are a helpful assistant for a storage management tool. Users
                        will ask you to manage the placement of data.

                        If you can answer without a tool, just provide the final answer. 
                        Otherwise, use the provided tools to help the user.  
                        
                        Once you receive the result of a tool call, revisit the user's original
                        query to see if this tool call is sufficient to answer or not.

                        Consider that the tool call's results can be used as input for another tool.
                """

        content, tool_calls = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            tools=self.tools,
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
