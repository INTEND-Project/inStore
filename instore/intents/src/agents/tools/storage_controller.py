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
        description="The command list as a string to run on the content and target storage environment."
    )


class StorageController(BaseTool):
    name: str = "StorageController"
    description: str = (
        """Takes a json list of commands that include identifiers, and timestamps to move, copy, and delete content around the storage environment. Example of input: {"commands":[{"cmd":"MOVE","destination":"AMSTERDAM_CACHE"", "source":"COLD_Storage", "date_time":"01-12-2025:12:00:00","content_id":"video0" },{"cmd":"DELETE","destination":"EU_CACHE_BERLIN_1","date_time":"01-12-2025:12:00:00", "content_id":"video1" }]}"""
    )

    def _run(self, commands: str, run_manager: Optional[CallbackManagerForToolRun] = None):
        try:
            cmds = json.loads(commands)
            v = None
            if type(cmds) is list:
                v = cmds
            else:
                v = cmds["commands"]
            for cmd in v:
                if cmd["source"] is None or cmd["source"] == "":
                    return "Source cannot be empty"
                if cmd["cmd"].lower() == "move" or cmd["cmd"].lower() == "copy":
                    if cmd["destination"] is None or cmd["destination"] == "":
                        return "'destination' cannot be empty in a move or copy command"
                    if cmd["source"] is None or cmd["source"] == "":
                        return "'source cannot be empty in a move or copy command"
            msg = "Commands have been sent successfully"
            pretty_print(msg, "Tool Message (Storage Controller)")
            return msg
        except Exception as err:
            pretty_print(title="Tool Message", msg=str(err))
            return str(err)
