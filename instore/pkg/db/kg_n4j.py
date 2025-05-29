import os
from typing import Any, Literal

from neo4j import Driver, GraphDatabase, Query, Record
from typing_extensions import LiteralString

from pkg.config import Neo4jKnowledgeGraphConfig
from pkg.interfaces import KnowledgeGraph


class Neo4jKnowledgeGraph(KnowledgeGraph):

    url = None
    driver: Driver

    def __init__(self, cfg: Neo4jKnowledgeGraphConfig):
        self.url = cfg.url
        self.driver = GraphDatabase.driver(
            self.url,
            auth=(
                os.environ.get("KNOWLEDGE_GRAPH_NEO4J_USERNAME", default="neo4j"),
                os.environ.get("KNOWLEDGE_GRAPH_NEO4J_PASSWORD", default="neo4j"),
            ),
        )

    def execute_query(self, query: str):
        q = Query("")
        q.text = query
        records, a, b = self.driver.execute_query(q)
        return records, a, b

    def get_intents(self) -> list[Record]:
        records, _, _ = self.driver.execute_query(
            """
                MATCH (i:Intent)-[r:RUNS]->(c:Command)
                RETURN i,c
                """
        )
        return records

    def create_intent(self, user_name: str, intent_name: str, commands: list[str]):
        with self.driver.session() as session:
            print(intent_name, user_name, commands)
            session.execute_write(self.__create_intent_tx, intent_name, user_name, commands)

    def create_user(self, user_name: str):
        self.driver.execute_query(
            """
            MERGE (u:User {name: $name})
            RETURN u.name as name
        """,
            name=user_name,
        )

    def create_application(self, application_name: str):
        self.driver.execute_query(
            """
                    MERGE (a:Application {name: $name})
                    RETURN a.name as name
                """,
            name=application_name,
        )

    def create_device(
        self,
        device_name: str,
        device_type: str,
        max_capacity_gb: str,
        allocated_capacity_gb: str,
        geolocation: str,
        backend: str,
    ):
        self.driver.execute_query(
            """
                MERGE (d:Device {
                                 type: $device_type,
                                 name: $name,
                                 max_capacity_gb: $max_capacity_gb,
                                 allocated_storage_gb: $allocated_storage_gb,
                                 geolocation: $geolocation,
                                 backend: $backend
                            }
                )
                RETURN d.name as name
            """,
            name=device_name,
            device_type=device_type,
            max_capacity_gb=max_capacity_gb,
            allocated_storage_gb=allocated_capacity_gb,
            geolocation=geolocation,
            backend=backend,
        )

    def delete_intent(self, intent_name: str):
        raise NotImplementedError("Delete intent not implemented yet")

    def __create_intent_tx(self, tx, intent_name: str, user_name: str, commands: list[str]):
        # Create INTENT
        result = tx.run(
            """
                        MERGE (i:Intent {name: $name})
                        RETURN i.name as name
            """,
            name=intent_name,
        )

        # Link INTENT to Command
        for cmd in commands:
            result = tx.run(
                """
                MERGE (c:Command {cmd: $cmd})
                RETURN c.cmd
                """,
                cmd=cmd,
            )
            result = tx.run(
                """
                    MATCH (i:Intent {name: $intent_name })
                    MATCH (c:Command {cmd: $cmd })
                    MERGE (i)-[r:RUNS]->(c)
                    RETURN i.name
                """,
                intent_name=intent_name,
                cmd=cmd,
            )

        return

    def get_topology(self, region: str = "all") -> list[dict[str, Any]]:
        records = None
        if region == "all":
            records, _, _ = self.driver.execute_query(
                """
                          MATCH (d:Device)
                          RETURN d as device
                """
            )

        else:
            records, _, _ = self.driver.execute_query(
                """
                        MATCH (d:Device {geolocation: $geolocation})
                        RETURN d as device
                """,
                geolocation=region,
            )
        return [self._node_to_dict(r["device"]) for r in records]

    def _node_to_dict(self, neo4j_node):
        props = {}
        for k, v in neo4j_node.items():
            props[k] = v
        return props
