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

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        user_prompt: str = str(messages)
        system_prompt = """You are a storage management agent. You monitor 2 storage nodes that are streaming large amounts of data to the cloud. Each of these nodes are running a Kafka instance.

        You will receive prompts from each of these nodes that tell you how much storage is currently allocated or free. Accordingly, you should:
            1. Ask the recommendation engine for suggested actions. Output will indicate whether to reduce Kafka retention period, increase Kafka retention period, or no change.
            2. When you receive a recommendation from step 1, this is now a new intent (which is like an objective for the system)
            3. Check whether the new intent conflicts with any existing intents.
            4. If a conflict is found, assess which conflicting intents should take priority and delete the other one.
            5. Send the storage controller the required parameters to make the necessary changes on the environment.
        """

        content, tool_calls = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
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
