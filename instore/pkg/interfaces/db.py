from abc import ABC, abstractmethod
from typing import Any


class KnowledgeGraph(ABC):
    @abstractmethod
    def create_intent(self, user_name: str, intent_name: str, affected_nodes: list[str]):
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
    def get_intents(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_topology(self, region: str = "all") -> list[dict[str, Any]]:
        pass
