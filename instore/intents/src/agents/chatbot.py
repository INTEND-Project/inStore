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
                    2. Use the check_conflicts tool to ensure that there is not an existing intent that conflicts with the extracted one (you cannot add REDUCE_COST intent if there is a REDUCE_LATENCY intent and vice versa). If a conflict is found, attempt to resolve the conflict with the user by asking them to choose between one of the two intents. 
                    3. When conflicts are resolved or are not found, pass the intent to the recommendation engine, which will output the path to a file that contains the new video locations recommended by the engine
                    4. Pass the file path to the Video Mover tool, which will handle all copy/move/delete operations
                    5. When the Video Mover tool succeeds:
                        a. Create the new intent by calling the create_intent tool with the objective (REDUCE_COST or REDUCE_LATENCY) and the same CSV file path passed to the Video Mover tool
                        b. Return the standard success JSON response including the intent name returned by create_intent and the action summary from the Video Mover tool as below:
                    {
                        "message": "Successfully created intent to decrease costs",
                        "intent_name": "reduce_cost_788f4760-5568-4bf1-8233-d9c8f62cd975",
                        "actions": "120 actions on 50 videos (20 moves, 60 copies, 40 purges), 2 actions failed"
                    }
                    6. When the Video Mover tool fails, return a descriptive text message on the error

                A few things to ensure:
                    - Make sure to delete intents with the delete_intent tool if conflict resolution dictates it
                    - Use the list_intents and get_intent tools to answer questions about existing intents
                    - Intent responses should only be json as specified, information retrieval responses should not be json
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
