from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field


class DataPlacementOptimizerInput(BaseModel):
    action: str = Field(
        description="The action for the tool to take, such as reducing latency or cost")
    content_tag: str = Field(
        description="The content tag to apply the action for, such as a video category")


class DataPlacementOptimizerTool(BaseTool):
    name: str = "DataPlacementOptimizer"
    description: str = "Takes decisions on where, when, and how to place data/content in a storage environment"
    args_schema: Optional[ArgsSchema] = DataPlacementOptimizerInput

    def _run(
            self,
            action: str,
            content_tag: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        # TODO: Use real data placement optimizer service
        return f"[DataPlacementOptimizer] {content_tag} videos are being moved to hot storage"
