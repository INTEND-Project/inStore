import os
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from neo4j import Driver, GraphDatabase, Record
from typing_extensions import LiteralString

from pkg.config import Neo4jKnowledgeGraphConfig
from pkg.interfaces import KnowledgeGraph


class Neo4jKnowledgeGraph(KnowledgeGraph):

    url = None
    driver: Driver

    def __init__(self, cfg: Neo4jKnowledgeGraphConfig):
        self.url = os.environ.get("KNOWLEDGE_GRAPH_NEO4J_URL") or cfg.url
        self.driver = GraphDatabase.driver(
            self.url,
            auth=(
                os.environ.get("KNOWLEDGE_GRAPH_NEO4J_USERNAME", default="neo4j"),
                os.environ.get("KNOWLEDGE_GRAPH_NEO4J_PASSWORD", default="neo4j"),
            ),
        )

    def get_conflicting_intents(
        self,
        objectives: list[str],
        start_time: str,
        end_time: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Return intents with one of the given objectives whose active period overlaps [start_time, end_time].

        An end of None or 'never' means open ended, and intents without dates are treated as always active.
        """
        records, _, _ = self.driver.execute_query(
            """
            MATCH (i:Intent)
            WHERE i.objective IN $objectives
            WITH i,
                 CASE WHEN i.from IS NULL THEN null ELSE datetime(i.from) END AS existingStart,
                 CASE WHEN i.to IS NULL OR i.to = 'never' THEN null ELSE datetime(i.to) END AS existingEnd,
                 datetime($start_time) AS newStart,
                 CASE WHEN $end_time IS NULL OR $end_time = 'never' THEN null ELSE datetime($end_time) END AS newEnd
            WHERE (existingStart IS NULL OR newEnd IS NULL OR existingStart <= newEnd)
              AND (existingEnd IS NULL OR newStart <= existingEnd)
            RETURN i
            """,
            objectives=objectives,
            start_time=start_time,
            end_time=end_time,
        )
        return [self._intent_to_dict(r["i"]) for r in records]

    def get_intents(self) -> list[dict[str, Any]]:
        records, _, _ = self.driver.execute_query(
            """
            MATCH (i:Intent)
            OPTIONAL MATCH (i)-[:RUNS]->(c:Command)
            RETURN i, collect(c) AS commands
            ORDER BY i.from
            """
        )
        return [self._intent_to_dict(r["i"], r["commands"]) for r in records]

    def get_intent(self, name: str) -> Optional[dict[str, Any]]:
        # OPTIONAL MATCH so intents without commands are still returned
        records, _, _ = self.driver.execute_query(
            """
            MATCH (i:Intent {name: $name})
            OPTIONAL MATCH (i)-[:RUNS]->(c:Command)
            RETURN i, collect(c) AS commands
            """,
            name=name,
        )
        if not records:
            return None
        return self._intent_to_dict(records[0]["i"], records[0]["commands"])

    def get_device(self, name) -> object:
        records, _, _ = self.driver.execute_query(
            "MATCH (d:Device {name: $name}) LIMIT 1 RETURN d",
            name=name,
        )
        return [r.data() for r in records][0]["d"]

    def create_intent(
        self,
        objective: str,
        commands: list[dict[str, str]],
        start_from: Optional[str] = None,
        end_at: str = "never",
    ) -> str:
        """Create an intent and one Command node per command, linked only to this intent. Returns the intent name."""
        name = f"{objective.lower()}_{uuid.uuid4()}"
        start_from = start_from or datetime.now(timezone.utc).isoformat(timespec="seconds")
        # A single query runs in a single transaction, so the intent and its commands are created together
        self.driver.execute_query(
            """
            CREATE (i:Intent {name: $name, objective: $objective, from: $start_from, to: $end_at})
            WITH i
            UNWIND $commands AS cmd
            CREATE (i)-[:RUNS]->(:Command {
                cmd: cmd.cmd,
                content_id: cmd.content_id,
                date_time: cmd.date_time,
                source: cmd.source,
                destination: cmd.destination
            })
            """,
            name=name,
            objective=objective,
            start_from=start_from,
            end_at=end_at,
            commands=commands,
        )
        return name

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

    def delete_intent(self, intent_name: str) -> bool:
        """Delete an intent and its commands. Returns False if the intent does not exist."""
        _, summary, _ = self.driver.execute_query(
            """
            MATCH (i:Intent {name: $name})
            OPTIONAL MATCH (i)-[:RUNS]->(c:Command)
            DETACH DELETE c, i
            """,
            name=intent_name,
        )
        return summary.counters.nodes_deleted > 0

    def get_topology(self, region: str = "ALL") -> list[dict[str, Any]]:
        records = None
        if region.upper() == "ALL":
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

    @staticmethod
    def _intent_to_dict(intent_node, command_nodes=()) -> dict[str, Any]:
        return {
            "name": intent_node.get("name"),
            "objective": intent_node.get("objective"),
            "from": intent_node.get("from"),
            "to": intent_node.get("to"),
            "commands": [
                {k: c.get(k) for k in ("date_time", "cmd", "content_id", "source", "destination")}
                for c in command_nodes
            ],
        }

    def _node_to_dict(self, neo4j_node):
        props = {}
        for k, v in neo4j_node.items():
            props[k] = v
        return props
