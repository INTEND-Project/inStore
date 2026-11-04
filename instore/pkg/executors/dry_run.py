from pkg.interfaces import Action, ActionResult, Executor


class DryRunExecutor(Executor):
    """Logs actions instead of executing them, and reports each as succeeded."""

    dry_run = True

    def execute(self, actions: list[Action]) -> list[ActionResult]:
        for action in actions:
            print(f"[DRY RUN] {action.type} {action.content_id}: {action.source} -> {action.destination or '(purged)'}")
        return [ActionResult(action=action, ok=True) for action in actions]
