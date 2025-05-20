from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ArgsSchema, BaseTool, tool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph


class DataPlacementOptimizerInput(BaseModel):
    objective: str = Field(
        description="The objective for this tool to try to optimize towards, such as reducing latency or cost"
    )
    target: str = Field(description="The type of content to apply the action for, such as a video category")
    price_plan: str = Field(
        description="The current price being paid for storage for cache nodes, hot and cold storage"
    )
    devices: str = Field(
        description="The current available node names, and their average latency to access content from"
    )


class DataPlacementOptimizerTool(BaseTool):
    name: str = "RecommendationEngine"
    description: str = (
        "This tool is responsible for providing recommendations given inputs on the target environment and objectives."
    )
    args_schema: Optional[ArgsSchema] = DataPlacementOptimizerInput

    def _run(
        self,
        objective: str,
        target: str,
        price_plan: str,
        devices: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        # TODO: Use real data placement optimizer service
        return f"To achieve the objective {objective}. It is recommended to reducing hot storage allocation from 2TB to 1TB, this will decrease costs by 20% and increase average latency by 20ms"


class TopologyRetrieverInput(BaseModel):
    region: str = Field(description="Retrieve the topology for this specific geolocation/region.")


class TopologyRetriever(BaseTool):
    name: str = "TopologyRetriever"
    description: str = "Used to retrieve the topology of origin servers and cache nodes."

    knowledge_graph: KnowledgeGraph
    args_schema: Optional[ArgsSchema] = TopologyRetrieverInput

    def _run(self, region: str):
        return self.knowledge_graph.get_topology(region=region.lower())


class SimilarIntentRetrieverInput(BaseModel):
    intent_content: str = Field(
        description="The intent natural language so that all similar intents should be retrieved"
    )


class SimilarIntentRetriever(BaseTool):
    name: str = "SimilarIntentRetriever"
    description: str = "Fetches intents with similar or conflicting objectives"
    args_schema: Optional[ArgsSchema] = SimilarIntentRetrieverInput

    knowledge_graph: KnowledgeGraph

    def _run(self, intent_content: str) -> list[dict]:
        self.knowledge_graph.get_intents()
        return []


class AnalyticsTool(BaseTool):
    name: str = "AnalyticsTool"
    description: str = (
        "Retrieves analytics on the storage system, such as access patterns, cache hit/miss ratios, low/high demand videos, and storage cost plans and prices."
    )

    def _run(self):
        return str(
            {
                "costs_euro_per_gb_per_month": {
                    "cache": 0.25,
                    "origin_hot": 0.10,
                    "origin_cold": 0.01,
                },
                "avg_latency_ms": {
                    "EU_DUBLIN_CACHE_1": 80,
                    "EU_LIMERICK_CACHE_1": 40,
                    "EU_ORIGIN_HOT": 500,
                    "EU_ORIGIN_COLD": 2000,
                },
                "videos": {
                    "movies": {
                        "size_gb": 223,
                        "requests_in_last_hour": {
                            "EU_DUBLIN_CACHE_1": 12,
                            "EU_LIMERICK_CACHE_1": 2,
                            "EU_ORIGIN_HOT": 14,
                            "EU_ORIGIN_COLD": 0,
                        },
                        "requests_in_last_day": {
                            "EU_DUBLIN_CACHE_1": 100,
                            "EU_LIMERICK_CACHE_1": 50,
                            "EU_ORIGIN_HOT": 14,
                            "EU_ORIGIN_COLD": 1,
                        },
                        "requests_in_last_week": {
                            "EU_DUBLIN_CACHE_1": 500,
                            "EU_LIMERICK_CACHE_1": 125,
                            "EU_ORIGIN_HOT": 14,
                            "EU_ORIGIN_COLD": 4,
                        },
                        "requests_in_last_month": {
                            "EU_DUBLIN_CACHE_1": 2000,
                            "EU_LIMERICK_CACHE_1": 1000,
                            "EU_ORIGIN_HOT": 14,
                            "EU_ORIGIN_COLD": 6,
                        },
                    },
                    "vlogs": {
                        "size_gb": 176,
                        "requests_in_last_hour": {
                            "EU_DUBLIN_CACHE_1": 0,
                            "EU_LIMERICK_CACHE_1": 5,
                            "EU_ORIGIN_HOT": 12,
                            "EU_ORIGIN_COLD": 10,
                        },
                        "requests_in_last_day": {
                            "EU_DUBLIN_CACHE_1": 12,
                            "EU_LIMERICK_CACHE_1": 24,
                            "EU_ORIGIN_HOT": 12,
                            "EU_ORIGIN_COLD": 1,
                        },
                        "requests_in_last_week": {
                            "EU_DUBLIN_CACHE_1": 40,
                            "EU_LIMERICK_CACHE_1": 80,
                            "EU_ORIGIN_HOT": 12,
                            "EU_ORIGIN_COLD": 1,
                        },
                        "requests_in_last_month": {
                            "EU_DUBLIN_CACHE_1": 100,
                            "EU_LIMERICK_CACHE_1": 200,
                            "EU_ORIGIN_HOT": 12,
                            "EU_ORIGIN_COLD": 1,
                        },
                    },
                },
            }
        )
