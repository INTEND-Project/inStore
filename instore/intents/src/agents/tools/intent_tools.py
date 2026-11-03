import csv
import json
import os
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph
from pkg.utils.pretty_print import pretty_print

from .mog_video_mover import classify_action

# Objectives that cannot be active at the same time
CONFLICTING_OBJECTIVES = {
    "REDUCE_COST": ["REDUCE_LATENCY"],
    "REDUCE_LATENCY": ["REDUCE_COST"],
}

OBJECTIVE_DESCRIPTION = 'The intent objective, either "REDUCE_COST" or "REDUCE_LATENCY"'


def _check_objective(objective: str):
    if objective not in CONFLICTING_OBJECTIVES:
        raise ValueError(f"Unknown objective {objective}, supported objectives are {list(CONFLICTING_OBJECTIVES)}")


class ListIntents(BaseTool):
    name: str = "list_intents"
    description: str = "Lists the intents stored in the intent database with their objective, active period, and number of commands"
    knowledge_graph: KnowledgeGraph

    def _run(self) -> str:
        intents = [
            {"name": i["name"], "objective": i["objective"], "from": i["from"], "to": i["to"], "commands": len(i["commands"])}
            for i in self.knowledge_graph.get_intents()
        ]
        pretty_print(f"Found {len(intents)} intents", "Tool Message (List Intents)")
        return json.dumps(intents)


class IntentNameInput(BaseModel):
    name: str = Field(description="The name of the intent")


class GetIntent(BaseTool):
    name: str = "get_intent"
    description: str = "Returns an intent from the intent database, including the commands (video actions) it ran"
    args_schema: Optional[ArgsSchema] = IntentNameInput
    knowledge_graph: KnowledgeGraph

    def _run(self, name: str) -> str:
        intent = self.knowledge_graph.get_intent(name)
        if intent is None:
            return f"Intent {name} not found"
        return json.dumps(intent)


class ObjectiveInput(BaseModel):
    objective: str = Field(description=OBJECTIVE_DESCRIPTION)


class CheckConflicts(BaseTool):
    name: str = "check_conflicts"
    description: str = "Returns the existing intents that conflict with a new intent with the given objective"
    args_schema: Optional[ArgsSchema] = ObjectiveInput
    knowledge_graph: KnowledgeGraph

    def _run(self, objective: str) -> str:
        _check_objective(objective)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conflicts = self.knowledge_graph.get_conflicting_intents(CONFLICTING_OBJECTIVES[objective], now)
        pretty_print(f"Found {len(conflicts)} conflicting intents for {objective}", "Tool Message (Check Conflicts)")
        if not conflicts:
            return "No conflicting intents"
        return json.dumps([{"name": i["name"], "objective": i["objective"]} for i in conflicts])


class CreateIntentInput(BaseModel):
    objective: str = Field(description=OBJECTIVE_DESCRIPTION)
    csv_file_path: str = Field(description="Path to the CSV file of video actions that was passed to the video mover")


class CreateIntent(BaseTool):
    name: str = "create_intent"
    description: str = (
        "Creates a new intent in the intent database with the video actions from the CSV file, returns the name of the created intent"
    )
    args_schema: Optional[ArgsSchema] = CreateIntentInput
    knowledge_graph: KnowledgeGraph

    def _run(self, objective: str, csv_file_path: str) -> str:
        _check_objective(objective)
        if not os.path.exists(csv_file_path):
            raise ValueError(f"CSV file {csv_file_path} not found")

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        commands = []
        with open(csv_file_path, "r", newline="", encoding="utf-8") as csvfile:
            for row in csv.reader(csvfile, delimiter=","):
                if len(row) < 3:
                    continue
                source, destination = row[1].strip(), row[2].strip()
                commands.append(
                    {
                        "cmd": classify_action(source, destination),
                        "content_id": row[0].strip(),
                        "source": source,
                        "destination": destination,
                        "date_time": now,
                    }
                )

        name = self.knowledge_graph.create_intent(objective=objective, commands=commands, start_from=now)
        pretty_print(f"Created intent {name} with {len(commands)} commands", "Tool Message (Create Intent)")
        return json.dumps({"intent_name": name, "commands": len(commands)})


class DeleteIntent(BaseTool):
    name: str = "delete_intent"
    description: str = "Deletes an intent and its commands from the intent database"
    args_schema: Optional[ArgsSchema] = IntentNameInput
    knowledge_graph: KnowledgeGraph

    def _run(self, name: str) -> str:
        deleted = self.knowledge_graph.delete_intent(name)
        pretty_print(f"Deleted intent {name}: {deleted}", "Tool Message (Delete Intent)")
        return f"Deleted intent {name}" if deleted else f"Intent {name} not found"


def intent_tools(knowledge_graph: KnowledgeGraph) -> list[BaseTool]:
    return [
        ListIntents(knowledge_graph=knowledge_graph),
        GetIntent(knowledge_graph=knowledge_graph),
        CheckConflicts(knowledge_graph=knowledge_graph),
        CreateIntent(knowledge_graph=knowledge_graph),
        DeleteIntent(knowledge_graph=knowledge_graph),
    ]
