from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import RecommendationEngine as Engine
from pkg.utils.pretty_print import pretty_print

from .actions_csv import RECOMMENDATIONS_CSV_PATH, write_actions_csv


class RecommendationEngineInput(BaseModel):
    intent: str = Field(description='The intent or objective to achieve, can be "REDUCE_COST" or "REDUCE_LATENCY"')


class RecommendationEngine(BaseTool):
    name: str = "recommendation_engine"
    description: str = (
        "This tool is responsible for providing the system state and location of videos for reducing latency or costs on the target environment, it creates a CSV file with the videos, their current locations, and their recommended locations"
    )
    engine: Engine

    def _run(self, intent: str):
        actions = self.engine.recommend(objective=intent)
        write_actions_csv(actions, RECOMMENDATIONS_CSV_PATH)
        pretty_print(f"CSV File Path: '{RECOMMENDATIONS_CSV_PATH}'", "Tool Message (Recommendation Engine)")
        return f"CSV File Path: '{RECOMMENDATIONS_CSV_PATH}'"
