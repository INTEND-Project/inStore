from typing import Optional

import requests

from pkg.interfaces import Action, ActionResult, Executor


class MogExecutor(Executor):
    """Executes actions through the MOG API."""

    dry_run = False

    def __init__(self, api_url: Optional[str]):
        self.api_url = api_url

    def execute(self, actions: list[Action]) -> list[ActionResult]:
        if not self.api_url:
            raise ValueError("MOG_API_URL is not set")
        results = []
        for action in actions:
            try:
                self._execute_one(action).raise_for_status()
                results.append(ActionResult(action=action, ok=True))
            except Exception as e:
                results.append(ActionResult(action=action, ok=False, error=str(e)))
        return results

    def _execute_one(self, action: Action) -> requests.Response:
        if action.type == "purge":
            return requests.post(
                f"{self.api_url}/files/purge",
                {"file": action.content_id, "region": action.source},
                timeout=10,
            )
        if action.type == "move":
            return requests.post(
                f"{self.api_url}/files/move",
                {"file": action.content_id, "destination": action.destination, "source": action.source},
                timeout=10,
            )
        if action.type == "copy":
            return requests.get(
                f"{self.api_url}/files/copy",
                {"region": action.destination, "file": action.content_id},
                timeout=10,
            )
        raise ValueError(f"Unsupported action type {action.type}")
