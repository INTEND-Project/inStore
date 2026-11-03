import os
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from pkg.interfaces import LLM


class Chatbot(BaseChatModel):

    llm: LLM
    tools: Sequence[BaseTool]
    # Built from the use case by build_system_prompt
    system_prompt: str

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        user_prompt: str = str(messages)
        content, tool_calls = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            tools=self.tools,
        )
        message = AIMessage(content=content, tool_calls=tool_calls)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.llm.get_model()}

    @property
    def _llm_type(self) -> str:
        return "custom"
