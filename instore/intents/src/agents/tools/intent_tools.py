import json
from typing import Optional

from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import RecommendationEngine
from pkg.utils.pretty_print import pretty_print
from src.errors import NotFound, ServiceError
from src.service import IntentService

OBJECTIVE_DESCRIPTION = "The intent objective, one of the supported objectives listed in the tool description"


def supported_objectives(engine: RecommendationEngine) -> str:
    return "Supported objectives: " + ", ".join(o.name for o in engine.objectives)


class ListIntents(BaseTool):
    name: str = "list_intents"
    description: str = "Lists the intents stored in the intent database with their objective, active period, and number of commands"
    service: IntentService

    def _run(self) -> str:
        intents = [
            {"name": i["name"], "objective": i["objective"], "from": i["from"], "to": i["to"], "commands": len(i["commands"])}
            for i in self.service.list_intents()
        ]
        pretty_print(f"Found {len(intents)} intents", "Tool Message (List Intents)")
        return json.dumps(intents)


class IntentNameInput(BaseModel):
    name: str = Field(description="The name of the intent")


class GetIntent(BaseTool):
    name: str = "get_intent"
    description: str = "Returns an intent from the intent database, including the commands (storage actions) it ran"
    args_schema: Optional[ArgsSchema] = IntentNameInput
    service: IntentService

    def _run(self, name: str) -> str:
        try:
            return json.dumps(self.service.get_intent(name))
        except NotFound as e:
            return e.message


class ObjectiveInput(BaseModel):
    objective: str = Field(description=OBJECTIVE_DESCRIPTION)


class CheckConflicts(BaseTool):
    name: str = "check_conflicts"
    description: str = "Returns the existing intents that conflict with a new intent with the given objective"
    args_schema: Optional[ArgsSchema] = ObjectiveInput
    service: IntentService

    def _run(self, objective: str) -> str:
        try:
            conflicts = self.service.check_conflicts(objective)
        except ServiceError as e:
            return e.message
        pretty_print(f"Found {len(conflicts)} conflicting intents for {objective}", "Tool Message (Check Conflicts)")
        if not conflicts:
            return "No conflicting intents"
        return json.dumps([{"name": i["name"], "objective": i["objective"]} for i in conflicts])


class DeleteIntent(BaseTool):
    name: str = "delete_intent"
    description: str = "Deletes an intent and its commands from the intent database"
    args_schema: Optional[ArgsSchema] = IntentNameInput
    service: IntentService

    def _run(self, name: str) -> str:
        try:
            self.service.delete_intent(name)
        except NotFound as e:
            return e.message
        pretty_print(f"Deleted intent {name}", "Tool Message (Delete Intent)")
        return f"Deleted intent {name}"


def intent_tools(service: IntentService) -> list[BaseTool]:
    return [
        ListIntents(service=service),
        GetIntent(service=service),
        CheckConflicts(
            service=service,
            description=f"{CheckConflicts.model_fields['description'].default}. {supported_objectives(service.engine)}",
        ),
        DeleteIntent(service=service),
    ]
