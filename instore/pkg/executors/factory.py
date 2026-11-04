import os

from pkg.config import ComponentInfo
from pkg.interfaces import Executor

from .dry_run import DryRunExecutor
from .mog import MogExecutor


def executor_factory(info: ComponentInfo, dry_run: bool) -> Executor:
    """Creates the executor selected in the use_case section of the config file, or the dry run executor."""
    if dry_run:
        return DryRunExecutor()
    if info.provider == "mog":
        return MogExecutor(api_url=os.environ.get("MOG_API_URL"))
    raise ValueError(f"Unknown executor {info.provider}")
