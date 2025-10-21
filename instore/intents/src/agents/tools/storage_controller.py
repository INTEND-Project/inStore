import json
from types import TracebackType
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print


class StorageControllerInput(BaseModel):
    commands: str = Field(
        description='The commands to run on the target storage environment in json format e.g., {"command":"reduce_ttl","value":"24hrs"}'
    )


class StorageController(BaseTool):
    name: str = "StorageController"
    description: str = "Runs commands on the storage environment"

    def _run(self, commands: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        msg = "Commands have been sent successfully: " + commands
        pretty_print(msg, "Tool Message (Storage Controller)")
        return msg
