import os
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
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
        system_prompt = """You are a helpful assistant for a user's storage management environment. Users may ask for information, 
            request specific actions to be made, or optimize the system towards cost or latency. You do not need to use all tools.

            When you receive a prompt, do the following steps:
                1. If only information is requested, consider using the topology and analytics tools.
                2. Use intent database to get all intents to ensure that this intent is not similar or contradictory to other intents. If a conflict has been found,
                   suggesting alternatives but do not take action on your own:
                        a. Remove old intent in favor of the new one
                        b. Cancel the new intent, ask if you can help with anything else if this is case
                        c. Suggest different dates to apply the new intent, or change the dates of the old intent. Suggest the dates yourself do not ask the user to do so.
                        d. Balances between 'reduce_latency' and 'reduce_costs' by passing 'balanced' to the recommendation engine.
                3. If moving videos is required, consider using the topology and analytics tool to find the source node of the video, 
                   then use their output as input to the storage controller tool.
                4. If optimization towards costs or latency is required, use outputs from the topology and analytics tools, then call the recommendation engine tool
                   to get the list of commands that will achieve the request's objectives, then send these commands to the storage controller tool.
                5. Create the intent
                6. If an action has been taken and you believe you have achieved the user's request, 
                   respond giving only a summary in json format of the actions to be taken as 'intents'. Example:
                    {
                        "message": "Successfully created intent to decrease costs",
                        "intent_name": "reduce_cost_sept_2025_dublin",
                        "actions": "videos [video123,video456] being moved to cold storage [EU_ORIGIN_COLD_1]",
                        "results": "latency to be increased by 20ms, costs saved during September 2025 are 20 Euros"
                    }
                   Successfully created intent to decrease costs:
                    ### Intent#1234
                    **Actions taken**: Videos [video123, video456] being moved to cheaper storage.
                    **Results**: e.g, Latency to be increased by 20ms, costs saved for this month 20 euros (infer the values from analytics result)

                A few things to ensure:
                    - If you delete an intent, make sure to delete the Commands associated with it as well
                    - Intent responses should only be json as specified
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
