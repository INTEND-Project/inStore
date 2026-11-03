import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from pkg.interfaces import Action


class PlanError(Exception):
    pass


@dataclass
class Plan:
    id: str
    objective: str
    # Copied from the engine's objective, so executing the plan does not depend on the engine
    conflicts_with: list[str]
    actions: list[Action]
    created_at: datetime
    executed_at: Optional[datetime] = None
    intent_name: Optional[str] = None


class PlanStore:
    """Keeps recommended plans in memory until they are executed or expire.

    Plans live as long as the conversation that confirms them, which is also kept in memory.
    """

    def __init__(self, ttl_seconds: int = 30 * 60):
        self._ttl = timedelta(seconds=ttl_seconds)
        self._plans: dict[str, Plan] = {}
        self._lock = threading.Lock()

    def add(self, objective: str, conflicts_with: list[str], actions: list[Action]) -> Plan:
        now = datetime.now(timezone.utc)
        plan = Plan(id=str(uuid.uuid4()), objective=objective, conflicts_with=conflicts_with, actions=actions, created_at=now)
        with self._lock:
            # Drop expired plans that were never executed
            self._plans = {k: p for k, p in self._plans.items() if p.executed_at or now - p.created_at <= self._ttl}
            self._plans[plan.id] = plan
        return plan

    def claim(self, plan_id: str) -> Plan:
        """Marks a plan as executing, so it cannot be executed twice."""
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                raise PlanError(f"Plan {plan_id} not found, recommend a new plan")
            if plan.executed_at is not None:
                raise PlanError(f"Plan {plan_id} was already executed as intent {plan.intent_name}")
            if datetime.now(timezone.utc) - plan.created_at > self._ttl:
                raise PlanError(f"Plan {plan_id} expired, recommend a new plan")
            plan.executed_at = datetime.now(timezone.utc)
            return plan

    def release(self, plan_id: str):
        """Allows a plan to be executed again after its execution failed before any action ran."""
        with self._lock:
            if plan_id in self._plans:
                self._plans[plan_id].executed_at = None
