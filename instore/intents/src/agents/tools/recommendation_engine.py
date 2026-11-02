import json
import os
from datetime import date
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print

from .recommend import plan

MOCK_VIDEOS_PATH = os.path.join(os.path.dirname(__file__), "mock_data", "mog_videos.json")


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

        if os.environ.get("MOG_DRY_RUN", "").lower() in ("true", "1"):
            with open(MOCK_VIDEOS_PATH, "r", encoding="utf-8") as f:
                videos = json.load(f)
            pretty_print(f"[DRY RUN] Using mock videos from '{MOCK_VIDEOS_PATH}'", "Tool Message (Recommendation Engine)")
            plan(mode=intent, out_csv=csv_file_path, videos=videos)
            return f"CSV File Path: '{csv_file_path}'"

        api_base_url = os.environ.get("MOG_API_URL")
        if not api_base_url:
            raise ValueError("MOG_API_URL is not set")

        plan(mode=intent, base_url=f"{api_base_url}/videos", out_csv=csv_file_path)
        return f"CSV File Path: '{csv_file_path}'"
