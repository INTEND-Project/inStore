import json
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class StorageControllerInput(BaseModel):
    commands: str = Field(
        description="""The command list to run on the content. (e.g.,
         '[{"cmd":"MOVE","destination":"EU_CACHE_BERLIN_1", "source":"EU_ORIGIN_COLD", "date_time":"01-12-2025:12:00:00" }'])"""
    )


class StorageController(BaseTool):
    name: str = "StorageController"
    description: str = (
        "Takes a list of commands that include identifiers, and timestamps to move, copy, and delete content around the storage environment"
    )

    def _run(self, commands: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        cmds = json.loads(commands)
        for cmd in cmds:
            if cmd["source"] is None or cmd["source"] == "":
                return "Source cannot be empty"
            if cmd["cmd"].lower() == "move" or cmd["cmd"].lower() == "copy":
                if cmd["destination"] is None or cmd["destination"] == "":
                    return "'destination' cannot be empty in a move or copy command"
                if cmd["source"] is None or cmd["source"] == "":
                    return "'source cannot be empty in a move or copy command"
        return "Commands have been sent successfully"
