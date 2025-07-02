from abc import ABC, abstractmethod
from typing import Any

from neo4j import Record


class KnowledgeGraph(ABC):
    @abstractmethod
    def create_intent(
        self, intent_name: str, start_from: str, end_at: str, objective: str, commands: list[dict[str, str]]
    ):
        pass

    @abstractmethod
    def delete_intent(self, intent_name: str):
        pass

    @abstractmethod
    def create_application(self, application_name: str):
        pass

    @abstractmethod
    def create_device(
        self,
        device_name: str,
        device_type: str,
        max_capacity_gb: str,
        allocated_capacity_gb: str,
        geolocation: str,
        backend: str,
    ):
        pass

    @abstractmethod
    def create_user(self, user_name: str):
        pass

    @abstractmethod
    def get_intents(self) -> list[object]:
        pass

    @abstractmethod
    def get_conflicting_intents(self, start_time: str, end_time: str, objective: str) -> list[object]:
        pass

    @abstractmethod
    def get_intent(self, name: str) -> object:
        pass

    @abstractmethod
    def get_device(self, name: str) -> object:
        pass

    @abstractmethod
    def get_topology(self, region: str = "ALL") -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Any:
        pass
