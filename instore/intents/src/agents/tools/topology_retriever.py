from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph


class TopologyRetrieverInput(BaseModel):
    region: str = Field(
        description="Retrieve the topology for this specific geolocation/region. 'all' if not specified. This includes nodes, storage space, types, geolocations, etc."
    )


class TopologyRetriever(BaseTool):
    name: str = "TopologyRetriever"
    description: str = "Used to retrieve the topology of origin servers and cache nodes."

    knowledge_graph: KnowledgeGraph
    args_schema: Optional[ArgsSchema] = TopologyRetrieverInput

    def _run(self, region: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        return self.knowledge_graph.get_topology(region=region.lower())
