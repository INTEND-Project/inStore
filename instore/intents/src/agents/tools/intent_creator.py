import json
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph
from pkg.utils.pretty_print import pretty_print


class IntentCreatorInput(BaseModel):
    intent_name: str = Field(description="The name of the intent (e.g., reduce_cost_sep2025)")
    start_timestamp: str = Field(
        description="The timestamp that the intend will take place on (e.g., 2024-06-01T00:00:00)"
    )
    end_timestamp: str = Field(
        description="The timestamp for the last command to take place for this intent (e.g., 2025-06-01T00:00:00)"
    )
    objective: str = Field(description="Either reduce_cost, reduce_latency")
    commands: str = Field(
        description="""
        The list of commands that are going to be executed as a side effect of this intent. It should be in the in the following json schema:
        {"commands": [{"cmd": "MOVE", "source": "EU_ORIGIN_HOT_1", "destination": "EU_ORIGIN_COLD_1", "content_id": "videoxyz", "date_time": "2025-06-20T11:29:53"}]}
        """
    )


class IntentCreator(BaseTool):
    name: str = "IntentCreator"
    description: str = "Creates a new intent"

    knowledge_graph: KnowledgeGraph

    def _run(
        self,
        intent_name: str,
        start_timestamp: str,
        end_timestamp: str,
        objective: str,
        commands: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        cmds = json.loads(commands)
        msg = str(
            self.knowledge_graph.create_intent(
                intent_name=intent_name,
                start_from=start_timestamp,
                end_at=end_timestamp,
                objective=objective,
                commands=cmds["commands"],
            )
        )
        pretty_print(msg, "Tool Message (Intent Creator)")
        return msg
