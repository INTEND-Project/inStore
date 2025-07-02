from datetime import date
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import ToolMessage
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print


class RecommendationEngineInput(BaseModel):
    objective: str = Field(description="Possible values are 'reduce_cost', 'reduce_latency', 'custom'")
    video_location_pairs: list[str] = Field(
        description="""The list of video ID and their node locations (e.g., ["video123,EU_ORIGIN_COLD", "video456,HOT_STORAGE"] ) that an action
            needs to be taken on. For system-wide objectives, all video IDs should be added here."""
    )
    devices: list[str] = Field(
        description="The list of current available nodes names, origin cold and hot storage should always be included."
    )
    from_timestamp: str = Field(
        description="The datetime at which the objective should be achieved. If no timeframe is available, use 'now'"
    )
    to_timestamp: str = Field(
        description="The datetime at which the objective should no longer be seeked. If no end time available, leave empty"
    )


class RecommendationEngine(BaseTool):
    name: str = "RecommendationEngine"
    description: str = (
        "This tool is responsible for providing the recommended commands for reducing latency or costs on the target environment, intents still need to be created in the database using these commands"
    )
    args_schema: Optional[ArgsSchema] = RecommendationEngineInput

    def _run(
        self,
        objective: str,
        video_location_pairs: list[str],
        devices: list[str],
        from_timestamp: str,
        to_timestamp: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        commands: list[dict[str, str]] = []
        cold_storage_devices, hot_storage_devices, cache_devices = [], [], []
        for d in devices:
            if "cache" in d.lower():
                cache_devices.append(d)
            elif "cold" in d.lower():
                cold_storage_devices.append(d)
            else:
                hot_storage_devices.append(d)

        _from = date.today().isoformat() if from_timestamp == "now" else from_timestamp
        to = to_timestamp if to_timestamp is not None and to_timestamp != "" else "never"
        if objective == "reduce_latency":
            for pair in video_location_pairs:
                video_id, location = pair.split(",")
                if "cold" in location.lower():
                    commands.append(
                        {
                            "date_time": _from,
                            "cmd": "MOVE",
                            "source": location,
                            "destination": hot_storage_devices[0],
                            "content_id": video_id,
                        }
                    )
                    if to_timestamp != "never":
                        commands.append(
                            {
                                "date_time": to,
                                "cmd": "MOVE",
                                "source": hot_storage_devices[0],
                                "destination": location,
                                "content_id": video_id,
                            }
                        )
                elif "cache" in location.lower():
                    continue
                elif "hot" in location.lower():
                    commands.append(
                        {
                            "date_time": _from,
                            "cmd": "MOVE",
                            "source": location,
                            "destination": cache_devices[0],
                            "content_id": video_id,
                        }
                    )

                    if to_timestamp != "never":
                        commands.append(
                            {
                                "date_time": to,
                                "cmd": "MOVE",
                                "source": cold_storage_devices[0],
                                "destination": location,
                                "content_id": video_id,
                            }
                        )

        elif objective == "reduce_cost":
            for pair in video_location_pairs:
                video_id, location = pair.split(",")
                if "cache" in location.lower():
                    commands.append(
                        {
                            "date_time": _from,
                            "cmd": "MOVE",
                            "source": location,
                            "destination": hot_storage_devices[0],
                            "content_id": video_id,
                        }
                    )
                    if to_timestamp != "never":
                        commands.append(
                            {
                                "date_time": to,
                                "cmd": "MOVE",
                                "source": hot_storage_devices[0],
                                "destination": location,
                                "content_id": video_id,
                            }
                        )
                elif "cold" in location.lower():
                    continue
                elif "hot" in location.lower():
                    commands.append(
                        {
                            "date_time": _from,
                            "cmd": "MOVE",
                            "source": location,
                            "destination": cold_storage_devices[0],
                            "content_id": video_id,
                        }
                    )

                    if to_timestamp != "never":
                        commands.append(
                            {
                                "date_time": to,
                                "cmd": "MOVE",
                                "source": cold_storage_devices[0],
                                "destination": location,
                                "content_id": video_id,
                            }
                        )

        msg = str({"commands": str(commands)})
        pretty_print(f"{msg}...", "Tool Message (Recommendation Engine)")
        return msg
