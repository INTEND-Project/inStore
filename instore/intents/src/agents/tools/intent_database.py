from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph
from pkg.utils.pretty_print import pretty_print


class IntentDatabaseInput(BaseModel):
    cypher_query: str = Field(description="The Neo4j cypher query to update the intent database")


class IntentDatabase(BaseTool):
    name: str = "IntentDatabase"
    description: str = """
    Neo4j intent database. Use this to read, add, or delete. The following is the schema of the intent vertix (the only one): 
        (i: Intent {name: "reduce_latency_788f4760-5568-4bf1-8233-d9c8f62cd975", "objective": "REDUCE_LATENCY"})
        """
    args_schema: Optional[ArgsSchema] = IntentDatabaseInput

    knowledge_graph: KnowledgeGraph

    def _run(self, cypher_query: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        records, _, __ = self.knowledge_graph.execute_query(cypher_query)
        print(records)
        pretty_print(f"Successfully ran intent database query: {cypher_query}", "Tool Message (Intent Database)")
        return records
