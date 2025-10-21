from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from pkg.interfaces import KnowledgeGraph
from pkg.utils.pretty_print import pretty_print


class IntentUpdaterInput(BaseModel):
    cypher_query: str = "The Neo4j cypher query to update the intent database"


class IntentUpdater(BaseTool):
    name: str = "IntentDatabase"
    description: str = """
    Neo4j intent database. Use this to add and update intents. The following is an example of intent creation:
        CREATE (i:Intent {name: 'avoid_full_storage_node_1', objective: 'avoid_full_storage', timestamp: '2025-09-01T00:00:00'}) CREATE (c1:Command {cmd: 'REDUCE_TTL', date_time: '2025-05-30', destination: 'EDGE_NODE_1'}) CREATE (i)-[:RUNS]->(c1) CREATE (i)-[:RUNS]->(c2) MERGE (d1:Device {name: 'EDGE_NODE_1'}) MERGE (d2:Device {name: 'EDGE_NODE_2'}) CREATE (c1)-[:ON]->(d1) RETURN i.name
        """

    knowledge_graph: KnowledgeGraph

    def _run(self, cypher_query: str, run_manager: Optional[CallbackManagerForToolRun] = None):

        records, _, __ = self.knowledge_graph.execute_query(cypher_query)
        if len(records) > 0:
            pretty_print("Successfully created intent", "Tool Message (Intent Database)")
            return "Succesfully created intent"
        else:
            return "intent created"
