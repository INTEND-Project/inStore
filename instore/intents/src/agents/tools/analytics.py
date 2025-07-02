import os
from typing import Annotated, Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print

# class AnalyticsToolInput(BaseModel):
#    video_id: str = Field("Optional ID or name of video in question")
#    node_name: str = Field("Optional name of node in question")


class AnalyticsTool(BaseTool):
    name: str = "AnalyticsTool"
    description: str = (
        """Contains information on : 
            - video IDs and names 
            - where videos are hosted for deletion or movement requests 
            - video sizes
            - usage patterns and latency
            - cost for cold, hot, and cache storage per gb in euros.
        The tool takes no arguments.
        """
    )
    environment: dict[str, object]

    def _run(self):
        msg = str(self.environment)
        pretty_print(f"{msg[:100]}...", "Tool Message (Analytics)")
        return msg
