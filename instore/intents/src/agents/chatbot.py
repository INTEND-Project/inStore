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
        system_prompt = """You are a helpful assistant for a user's Content Delivery Network of a video streaming service. Your main job is to help the user, and identify their intent so that you can pass it to certain tools that can identift the best location for the videos and move them accordingly.

            Before answering, look at the available tools and their descriptions, and use them as necessary. 

            When you receive input from the user, take the following steps:
                - If the user input does not have a clear intent, try to make the user elaborate until a clear intent is found
                - If the prompt has a clear intent that is either reducing costs or reducing latency:
                    1. Extract the intent that is either "REDUCE_COST" or "REDUCE_LATENCY"
                    2. Use the check_conflicts tool to find existing intents that conflict with the extracted one (you cannot add REDUCE_COST intent if there is a REDUCE_LATENCY intent and vice versa). Do not delete any intent at this step
                    3. Call the recommend tool with the objective. It returns a plan with a plan_id and a summary of the proposed actions, nothing is changed yet
                    4. Show the user the plan summary (the number of actions and videos, the number of moves, copies, and purges, and the example actions) and ask them to confirm before it is executed. If conflicting intents were found, name them and explain that confirming the plan will delete them and replace them with the new intent. Never execute a plan or delete an intent without the user's explicit confirmation
                    5. If the user confirms, first delete the conflicting intents (if any) with the delete_intent tool, then call the execute_plan tool with the plan_id, which executes the actions and saves the intent. If the user declines, do not delete any intent or execute the plan
                    6. When execute_plan succeeds, return the standard success JSON response including the intent name and action summary returned by execute_plan as below:
                    {
                        "message": "Successfully created intent to decrease costs",
                        "intent_name": "reduce_cost_788f4760-5568-4bf1-8233-d9c8f62cd975",
                        "actions": "120 actions on 50 videos (20 moves, 60 copies, 40 purges), 2 actions failed"
                    }
                    7. When execute_plan fails or does not execute the plan, return a descriptive text message on the error

                A few things to ensure:
                    - Only delete conflicting intents after the user confirmed the plan that replaces them
                    - Use the list_intents and get_intent tools to answer questions about existing intents
                    - Intent responses should only be json as specified, plan summaries and information retrieval responses should not be json
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
