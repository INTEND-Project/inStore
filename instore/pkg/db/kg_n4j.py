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

    def get_conflicting_intents(
        self,
        start_time: str,
        end_time: str,
        objective: str,
    ):
        records, _, _ = self.driver.execute_query(
            """MATCH (intentInDb:Intent)
                WITH intentInDb,
                     datetime(intentInDb.from) AS existingStart,
                     CASE intentInDb.to
                          WHEN 'never' THEN null 
                          ELSE datetime(intentInDb.to)
                     END AS existingEnd,
                     datetime($start_date) AS newStart,
                     datetime($end_date) AS newEnd


                WHERE
                    
                    existingStart <= newEnd
                    AND
                    (existingEnd IS NULL OR newStart <= existingEnd)
                    AND
                    intentInDb.objective = $objective

                RETURN intentInDb as ConflictingIntent""",
            start_date=start_time,
            end_date=end_time,
            objective=objective,
        )

        intents = []
        for r in records:
            intents.append(r.data())
        return intents

    def get_intents(self) -> list[object]:
        records, _, _ = self.driver.execute_query(
            """
                MATCH (i:Intent)
                OPTIONAL MATCH (i:Intent)-[r:RUNS]->(c:Command)
                RETURN i,c
                """
        )
        intents = {}
        for record in records:
            data = record.data()
            intent_name = data["i"]["name"]
            if intent_name not in intents:
                intents[intent_name] = {
                    "from": data["i"]["from"],
                    "to": data["i"].get("to", "never"),
                    "objective": data["i"]["objective"],
                    "commands": [],
                }

            intent_commands: list[dict[str, str]] = intents[intent_name]["commands"]
            command = {}

            if data["c"] is not None:
                command = {
                    "date_time": data["c"]["date_time"],
                    "content_id": data["c"]["content_id"],
                    "destination": data["c"].get("destination", "none"),
                    "source": data["c"]["source"],
                    "cmd": data["c"]["cmd"],
                }
                if command not in intent_commands:
                    intent_commands.append(command)

                intents[intent_name]["commands"] = intent_commands

        intent_list = []
        for k, v in intents.items():
            v["name"] = k
            intent_list.append(v)
        return intent_list

    def get_intent(self, name) -> object:
        records, _, _ = self.driver.execute_query(
            """
            MATCH (i:Intent {name: $name})-[r:RUNS]->(c:Command)
                RETURN i,c
                """,
            name=name,
        )
        intents = {}
        for record in records:
            data = record.data()
            intent_name = data["i"]["name"]
            if intent_name not in intents:
                intents[intent_name] = {
                    "from": data["i"]["from"],
                    "to": data["i"]["to"],
                    "objective": data["i"]["objective"],
                    "commands": [],
                }

            intent_commands: list[dict[str, str]] = intents[intent_name]["commands"]
            command = {
                "date_time": data["c"]["date_time"],
                "content_id": data["c"]["content_id"],
                "destination": data["c"]["destination"],
                "source": data["c"]["source"],
                "cmd": data["c"]["cmd"],
            }
            if command not in intent_commands:
                intent_commands.append(command)

            intents[intent_name]["commands"] = intent_commands

        for _, v in intents.items():
            return v

    def get_device(self, name) -> object:
        records, _, _ = self.driver.execute_query(
            "MATCH (d:Device {name: $name}) LIMIT 1 RETURN d",
            name=name,
        )
        return [r.data() for r in records][0]["d"]

    def create_intent(
        self, intent_name: str, start_from: str, end_at: str, objective: str, commands: list[dict[str, str]]
    ):
        with self.driver.session() as session:
            session.execute_write(self.__create_intent_tx, intent_name, start_from, end_at, objective, commands)

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

    def __create_intent_tx(
        self,
        tx,
        intent_name: str,
        start_from: str,
        end_at: str,
        objective: str,
        commands: list[dict[str, str]],
    ):
        # Create INTENT
        tx.run(
            """
            MERGE (i:Intent {name: $name, from: $start_from, to: $end_at, objective: $objective})
                        RETURN i.name 
            """,
            name=intent_name,
            start_from=start_from,
            end_at=end_at,
            objective=objective,
        )

        # Link INTENT to Command
        for cmd in commands:
            tx.run(
                """
                MERGE (c:Command {
                    cmd: $cmd, 
                    content_id: $content_id, 
                    date_time: $date_time, 
                    destination: $destination, 
                    source: $source
                })
                RETURN c.cmd
                """,
                cmd=cmd["cmd"],
                content_id=cmd["content_id"],
                date_time=cmd["date_time"],
                destination=cmd["destination"],
                source=cmd["source"],
            )
            tx.run(
                """
                    MATCH (i:Intent {name: $intent_name })
                    MATCH (c:Command {cmd: $cmd })
                    MERGE (i)-[r:RUNS]->(c)
                    MERGE (c)-[o:ON_DEVICE]->(d:Device {name: $device_name})
                    RETURN i.name
                """,
                intent_name=intent_name,
                cmd=cmd["cmd"],
                device_name=cmd["destination"],
            )

        return

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

    def _node_to_dict(self, neo4j_node):
        props = {}
        for k, v in neo4j_node.items():
            props[k] = v
        return props
