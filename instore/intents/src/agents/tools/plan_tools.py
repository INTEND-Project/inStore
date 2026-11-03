import json
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import ActionResult, Executor, KnowledgeGraph, RecommendationEngine
from pkg.utils.pretty_print import pretty_print

from ..plans import PlanError, PlanStore
from .intent_tools import OBJECTIVE_DESCRIPTION, supported_objectives
EXAMPLE_ACTIONS = 5


class RecommendInput(BaseModel):
    objective: str = Field(description=OBJECTIVE_DESCRIPTION)


class Recommend(BaseTool):
    name: str = "recommend"
    description: str = (
        "Computes a plan of storage actions (moves, copies, and purges) that achieves the objective. "
        "Nothing is executed, returns a plan_id and a summary of the plan to show the user"
    )
    args_schema: Optional[ArgsSchema] = RecommendInput
    engine: RecommendationEngine
    plan_store: PlanStore

    def _run(self, objective: str) -> str:
        conflicts_with = self.engine.get_objective(objective).conflicts_with
        actions = self.engine.recommend(objective=objective)
        plan = self.plan_store.add(objective=objective, conflicts_with=conflicts_with, actions=actions)

        summary = {
            "plan_id": plan.id,
            "objective": objective,
            "actions": len(actions),
            self.engine.content_label: len({a.content_id for a in actions}),
            "by_type": dict(Counter(a.type for a in actions)),
            "example_actions": [
                f"{a.type} {a.content_id}: {a.source} -> {a.destination or '(purged)'}" for a in actions[:EXAMPLE_ACTIONS]
            ],
        }
        pretty_print(json.dumps(summary, indent=2), "Tool Message (Recommend)")
        return json.dumps(summary)


class ExecutePlanInput(BaseModel):
    plan_id: str = Field(description="The plan_id returned by the recommend tool, only after the user confirmed the plan")


class ExecutePlan(BaseTool):
    name: str = "execute_plan"
    description: str = (
        "Executes a plan confirmed by the user and saves it as a new intent, returns the intent name and a summary of the executed actions"
    )
    args_schema: Optional[ArgsSchema] = ExecutePlanInput
    executor: Executor
    knowledge_graph: KnowledgeGraph
    plan_store: PlanStore
    content_label: str = "items"

    def _run(self, plan_id: str) -> str:
        try:
            plan = self.plan_store.claim(plan_id)
        except PlanError as e:
            return f"Plan not executed: {e}"

        # Another conversation may have created a conflicting intent since the plan was recommended
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conflicts = self.knowledge_graph.get_conflicting_intents(plan.conflicts_with, now)
        if conflicts:
            self.plan_store.release(plan_id)
            names = ", ".join(f"{i['name']} ({i['objective']})" for i in conflicts)
            return f"Plan not executed: it conflicts with existing intents {names}, resolve the conflict with the user first"

        try:
            results = self.executor.execute(plan.actions)
        except Exception:
            self.plan_store.release(plan_id)
            raise

        summary = self._summary(results)
        pretty_print(summary, "Tool Message (Execute Plan)")
        if results and not any(r.ok for r in results):
            return f"Plan executed but all actions failed, no intent was saved: {summary}"

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
        pretty_print(f"Created intent {plan.intent_name} with {len(commands)} commands", "Tool Message (Execute Plan)")
        return json.dumps({"intent_name": plan.intent_name, "actions": summary})

    def _summary(self, results: list[ActionResult]) -> str:
        # Each result is one action (move, copy, or purge) on one content item, which can appear in several actions
        succeeded = {"move": 0, "copy": 0, "purge": 0}
        failed = 0
        items = set()
        for r in results:
            if r.ok:
                succeeded[r.action.type] = succeeded.get(r.action.type, 0) + 1
                items.add(r.action.content_id)
            else:
                pretty_print(f"{r.action}: {r.error}", "Tool Message (Execute Plan)")
                failed += 1

        summary = (
            f"{sum(succeeded.values())} actions on {len(items)} {self.content_label} "
            f"({succeeded['move']} moves, {succeeded['copy']} copies, {succeeded['purge']} purges), "
            f"{failed} actions failed"
        )
        if self.executor.dry_run:
            summary += " (dry run: simulated, no changes were made to the storage environment)"
        return summary


def plan_tools(
    engine: RecommendationEngine, executor: Executor, knowledge_graph: KnowledgeGraph, plan_store: PlanStore
) -> list[BaseTool]:
    return [
        Recommend(
            engine=engine,
            plan_store=plan_store,
            description=f"{Recommend.model_fields['description'].default}. {supported_objectives(engine)}",
        ),
        ExecutePlan(
            executor=executor, knowledge_graph=knowledge_graph, plan_store=plan_store, content_label=engine.content_label
        ),
    ]
