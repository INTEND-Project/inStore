import uuid
from typing import Any, Optional

from pkg.interfaces import Action, ActionResult, Executor, KnowledgeGraph


class InMemoryKnowledgeGraph(KnowledgeGraph):
    """Keeps intents in memory, for tests that do not need Neo4j."""

    def __init__(self, healthy: bool = True):
        self.intents: dict[str, dict[str, Any]] = {}
        self.healthy = healthy

    def create_intent(self, objective, commands, start_from=None, end_at="never") -> str:
        name = f"{objective.lower()}_{uuid.uuid4()}"
        self.intents[name] = {"name": name, "objective": objective, "from": start_from, "to": end_at, "commands": list(commands)}
        return name

    def delete_intent(self, intent_name: str) -> bool:
        return self.intents.pop(intent_name, None) is not None

    def get_intents(self) -> list[dict[str, Any]]:
        return list(self.intents.values())

    def get_intent(self, name: str) -> Optional[dict[str, Any]]:
        return self.intents.get(name)

    def get_conflicting_intents(self, objectives, start_time, end_time=None) -> list[dict[str, Any]]:
        # Intents created by the service are open ended, so any intent with a conflicting objective is active
        return [i for i in self.intents.values() if i["objective"] in objectives]

    def is_healthy(self) -> bool:
        return self.healthy

    def create_application(self, application_name): ...
    def create_device(self, *args, **kwargs): ...
    def create_user(self, user_name): ...
    def get_device(self, name): ...
    def get_topology(self, region="ALL"):
        return []


class FailingExecutor(Executor):
    """Reports every action as failed."""

    def execute(self, actions: list[Action]) -> list[ActionResult]:
        return [ActionResult(action=a, ok=False, error="HTTP 500") for a in actions]


class RaisingExecutor(Executor):
    """Fails before executing any action, like an unreachable storage environment."""

    def execute(self, actions: list[Action]) -> list[ActionResult]:
        raise ConnectionError("storage environment unreachable")
