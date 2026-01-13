from datetime import date
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print

from .recommend import plan


class RecommendationEngineInput(BaseModel):
    intent: str = Field(description='The intent or objective to achieve, can be "REDUCE_COST" or "REDUCE_LATENCY"')


class RecommendationEngine(BaseTool):
    name: str = "recommendation_engine"
    description: str = (
        "This tool is responsible for providing the system state and location of videos for reducing latency or costs on the target environment, it creates a CSV file with the videos, their current locations, and their recommended locations"
    )

    def _run(self, intent: str):
        csv_file_path = "/root/recommendations.csv"
        pretty_print(f"CSV File Path: '{csv_file_path}'", "Tool Message (Recommendation Engine)")
        plan(mode=intent, out_csv=csv_file_path)
        return f"CSV File Path: '{csv_file_path}'"
