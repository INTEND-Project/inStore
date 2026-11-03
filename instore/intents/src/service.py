from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from pkg.interfaces import ActionResult, Executor, KnowledgeGraph, Objective, RecommendationEngine
from pkg.utils.pretty_print import pretty_print

from .errors import ConflictingIntents, ExecutionFailed, InvalidRequest, NotFound, UpstreamError
from .plans import Plan, PlanStore

EXAMPLE_ACTIONS = 5


@dataclass
class ExecutionResult:
    intent_name: str
    summary: str
    results: list[ActionResult]


class IntentService:
    """Intent management shared by the agent's tools and the REST API."""

    def __init__(
        self,
        engine: RecommendationEngine,
        executor: Executor,
        knowledge_graph: KnowledgeGraph,
        plan_store: PlanStore,
        model_name: Optional[str] = None,
    ):
        self.engine = engine
        self.executor = executor
        self.knowledge_graph = knowledge_graph
        self.plan_store = plan_store
        self.model_name = model_name

    def capabilities(self) -> dict[str, Any]:
        return {
            "domain": self.engine.domain,
            "content_label": self.engine.content_label,
            "objectives": [
                {"name": o.name, "description": o.description, "conflicts_with": o.conflicts_with}
                for o in self.engine.objectives
            ],
            "recommendation_engine": type(self.engine).__name__,
            "executor": type(self.executor).__name__,
            "dry_run": self.executor.dry_run,
            "model": self.model_name,
        }

    def objective(self, name: str) -> Objective:
        try:
            return self.engine.get_objective(name)
        except ValueError as e:
            raise InvalidRequest(str(e))

    # Intents

    def list_intents(self, objective: Optional[str] = None) -> list[dict[str, Any]]:
        intents = self.knowledge_graph.get_intents()
        if objective is not None:
            intents = [i for i in intents if i["objective"] == objective]
        return intents

    def get_intent(self, name: str) -> dict[str, Any]:
        intent = self.knowledge_graph.get_intent(name)
        if intent is None:
            raise NotFound(f"Intent {name} not found")
        return intent

    def delete_intent(self, name: str):
        """Deletes the intent record, the storage changes made by its actions are not undone."""
        if not self.knowledge_graph.delete_intent(name):
            raise NotFound(f"Intent {name} not found")

    def check_conflicts(self, objective: str) -> list[dict[str, Any]]:
        conflicts_with = self.objective(objective).conflicts_with
        return self.knowledge_graph.get_conflicting_intents(conflicts_with, _now())

    # Plans

    def recommend(self, objective: str, params: Optional[dict] = None) -> Plan:
        conflicts_with = self.objective(objective).conflicts_with
        try:
            actions = self.engine.recommend(objective=objective, params=params)
        except Exception as e:
            raise UpstreamError(f"The recommendation engine failed: {e}")
        return self.plan_store.add(objective=objective, conflicts_with=conflicts_with, actions=actions)

    def plan_summary(self, plan: Plan) -> dict[str, Any]:
        return {
            "plan_id": plan.id,
            "objective": plan.objective,
            "actions": len(plan.actions),
            self.engine.content_label: len({a.content_id for a in plan.actions}),
            "by_type": dict(Counter(a.type for a in plan.actions)),
            "example_actions": [
                f"{a.type} {a.content_id}: {a.source} -> {a.destination or '(purged)'}"
                for a in plan.actions[:EXAMPLE_ACTIONS]
            ],
        }

    def execute_plan(self, plan_id: str) -> ExecutionResult:
        """Executes a plan and saves it as an intent with the result of each action."""
        plan = self.plan_store.claim(plan_id)

        # Another client may have created a conflicting intent since the plan was recommended
        now = _now()
        conflicts = self.knowledge_graph.get_conflicting_intents(plan.conflicts_with, now)
        if conflicts:
            self.plan_store.release(plan_id)
            names = ", ".join(f"{i['name']} ({i['objective']})" for i in conflicts)
            raise ConflictingIntents(
                f"Plan {plan_id} conflicts with existing intents {names}",
                details=[{"name": i["name"], "objective": i["objective"]} for i in conflicts],
            )

        try:
            results = self.executor.execute(plan.actions)
        except Exception as e:
            self.plan_store.release(plan_id)
            raise UpstreamError(f"The executor failed: {e}")

        summary = self.action_summary(results)
        pretty_print(summary, "Intent Service (Execute Plan)")
        if results and not any(r.ok for r in results):
            raise ExecutionFailed(f"All actions failed, no intent was saved: {summary}", details=_results(results))

        commands = [
            {
                "cmd": r.action.type,
                "content_id": r.action.content_id,
                "source": r.action.source,
                "destination": r.action.destination,
                "date_time": now,
                "status": "succeeded" if r.ok else "failed",
                "error": r.error,
            }
            for r in results
        ]
        plan.intent_name = self.knowledge_graph.create_intent(objective=plan.objective, commands=commands, start_from=now)
        pretty_print(f"Created intent {plan.intent_name} with {len(commands)} commands", "Intent Service (Execute Plan)")
        return ExecutionResult(intent_name=plan.intent_name, summary=summary, results=results)

    def action_summary(self, results: list[ActionResult]) -> str:
        # Each result is one action (move, copy, or purge) on one content item, which can appear in several actions
        succeeded = {"move": 0, "copy": 0, "purge": 0}
        failed = 0
        items = set()
        for r in results:
            if r.ok:
                succeeded[r.action.type] = succeeded.get(r.action.type, 0) + 1
                items.add(r.action.content_id)
            else:
                pretty_print(f"{r.action}: {r.error}", "Intent Service (Execute Plan)")
                failed += 1

        summary = (
            f"{sum(succeeded.values())} actions on {len(items)} {self.engine.content_label} "
            f"({succeeded['move']} moves, {succeeded['copy']} copies, {succeeded['purge']} purges), "
            f"{failed} actions failed"
        )
        if self.executor.dry_run:
            summary += " (dry run: simulated, no changes were made to the storage environment)"
        return summary


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _results(results: list[ActionResult]) -> list[dict[str, Any]]:
    return [
        {
            "type": r.action.type,
            "content_id": r.action.content_id,
            "source": r.action.source,
            "destination": r.action.destination,
            "status": "succeeded" if r.ok else "failed",
            "error": r.error,
        }
        for r in results
    ]
