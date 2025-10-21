from datetime import date
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print


class RecommendationEngineInput(BaseModel):
    total_storage_gb: str = Field(description="How much total storage is in the node.")
    allocated_storage_gb: str = Field(description="How much storage is currently allocated in the node.")


class RecommendationEngine(BaseTool):
    name: str = "RecommendationEngine"
    description: str = "This tool is responsible for providing the recommended commands to free up storage for a node."
    args_schema: Optional[ArgsSchema] = RecommendationEngineInput

    def _run(
        self,
        allocated_storage_gb: str,
        total_storage_gb: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        total_storage_int = int(total_storage_gb)
        allocated_storage_int = int(allocated_storage_gb)

        msg = ""
        if total_storage_int - allocated_storage_int < 1:
            msg = "command=reduce_ttl,value=1hrs"
        elif total_storage_int - allocated_storage_int > 100:
            msg = "command=reduce_ttl,value=24hrs"
        else:
            msg = "no action needed"
        pretty_print(f"{msg}...", "Tool Message (Recommendation Engine)")
        return msg
