from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from pkg.interfaces import KnowledgeGraph


class IntentDatabaseInput(BaseModel):
    cypher_query: str = "The Neo4j cypher query to interact with the database"


class IntentDatabase(BaseTool):
    name: str = "IntentDatabase"
    description: str = """
    Neo4j intent database. Here is an example of intent creation that shows the entire schema:
        CREATE (i:Intent {name: 'reduce_latency_dublin_sep2025', objective: 'reduce_latency', from: '2025-09-01:00:00:00', to: '2025-09-30:23:59:59'}) CREATE (c1:Command {cmd: 'MOVE', date_time: '2025-05-30', source: 'EU_ORIGIN_HOT', destination: 'EU_DUBLIN_CACHE_1', content_id: 'video456'}) CREATE (c2:Command {cmd: 'MOVE', date_time: '2025-05-30', source: 'EU_ORIGIN_COLD', destination: 'EU_ORIGIN_HOT', content_id: 'video456'}) CREATE (i)-[:RUNS]->(c1) CREATE (i)-[:RUNS]->(c2) MERGE (d1:Device {name: 'EU_ORIGIN_HOT'}) MERGE (d2:Device {name: 'EU_DUBLIN_CACHE_1'}) MERGE (d3:Device {name: 'EU_ORIGIN_COLD'}) CREATE (c1)-[:MOVE_FROM {video_ids: ['video456']}]->(d1) CREATE (c1)-[:MOVE_TO {video_ids: ['video456']}]->(d2) CREATE (c2)-[:MOVE_FROM {video_ids: ['video456']}]->(d3) CREATE (c2)-[:MOVE_TO {video_ids: ['video456']}]->(d1) RETURN i.name
        """

    knowledge_graph: KnowledgeGraph

    def _run(self, cypher_query: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        return str(self.knowledge_graph.execute_query(cypher_query))
