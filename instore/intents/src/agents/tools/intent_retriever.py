from datetime import date, datetime
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph
from pkg.utils.pretty_print import pretty_print


class IntentConflictDetectorInput(BaseModel):
    objective: str = Field(description="The new intent objective, can be 'reduce_cost' or 'reduce_latency'")
    start_date: str = Field(description="The date that the new intent starts")
    end_date: str = Field(description="The date that the new intent ends")


class IntentConflictDetector(BaseTool):
    name: str = "IntentConflictDetector"
    description: str = (
        """Takes intent date range and objective, and finds any conflicting intents in the same date range"""
    )
    knowledge_graph: KnowledgeGraph

    def _run(
        self, start_date: str, end_date: str, objective: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ):
        try:

            if objective == "reduce_cost":
                objective = "reduce_latency"
            if objective == "reduce_latency":
                objective = "reduce_cost"
            if start_date == "now":
                now = datetime.now()
                start_date = f"{now.year}-{now.month}-{now.day}T{now.hour}:{now.minute}:{now.second}"
            if end_date is None or end_date == "":
                end_date = "2100-30-12T11:59:59"
            intents = self.knowledge_graph.get_conflicting_intents(
                start_time=start_date, end_time=end_date, objective=objective
            )
            pretty_print(str(intents), "Tool Message (Conflict Detector)")
            if len(intents) == 0:
                return "No conflicting intents found"
            return intents
        except Exception as e:
            return "No conflicting intents found"
