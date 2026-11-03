import json
from typing import Optional

from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print
from src.errors import ConflictingIntents, ExecutionFailed, ServiceError
from src.service import IntentService

from .intent_tools import OBJECTIVE_DESCRIPTION, supported_objectives


class RecommendInput(BaseModel):
    objective: str = Field(description=OBJECTIVE_DESCRIPTION)


class Recommend(BaseTool):
    name: str = "recommend"
    description: str = (
        "Computes a plan of storage actions (moves, copies, and purges) that achieves the objective. "
        "Nothing is executed, returns a plan_id and a summary of the plan to show the user"
    )
    args_schema: Optional[ArgsSchema] = RecommendInput
    service: IntentService

    def _run(self, objective: str) -> str:
        try:
            plan = self.service.recommend(objective=objective)
        except ServiceError as e:
            return f"No plan computed: {e.message}"
        summary = self.service.plan_summary(plan)
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
    service: IntentService

    def _run(self, plan_id: str) -> str:
        try:
            result = self.service.execute_plan(plan_id)
        except ConflictingIntents as e:
            return f"Plan not executed: {e.message}, resolve the conflict with the user first"
        except ExecutionFailed as e:
            return f"Plan executed but {e.message[0].lower()}{e.message[1:]}"
        except ServiceError as e:
            return f"Plan not executed: {e.message}"
        return json.dumps({"intent_name": result.intent_name, "actions": result.summary})


def plan_tools(service: IntentService) -> list[BaseTool]:
    return [
        Recommend(
            service=service,
            description=f"{Recommend.model_fields['description'].default}. {supported_objectives(service.engine)}",
        ),
        ExecutePlan(service=service),
    ]
