from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Action:
    """A storage action, independent of the environment that executes it."""

    type: str  # "move", "copy", or "purge"
    content_id: str
    source: str
    destination: str = ""  # empty for purge


@dataclass
class Objective:
    name: str
    description: str
    conflicts_with: list[str] = field(default_factory=list)


class RecommendationEngine(ABC):
    """Decides which actions achieve an objective, without executing them."""

    objectives: list[Objective]

    @abstractmethod
    def recommend(self, objective: str, params: Optional[dict] = None) -> list[Action]:
        pass

    def get_objective(self, name: str) -> Objective:
        for objective in self.objectives:
            if objective.name == name:
                return objective
        raise ValueError(f"Unknown objective {name}, supported objectives are {[o.name for o in self.objectives]}")
