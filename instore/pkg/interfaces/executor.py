from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .engine import Action


@dataclass
class ActionResult:
    action: Action
    ok: bool
    error: Optional[str] = None


class Executor(ABC):
    """Executes actions on a storage environment and reports the result of each."""

    dry_run: bool = False

    @abstractmethod
    def execute(self, actions: list[Action]) -> list[ActionResult]:
        pass
