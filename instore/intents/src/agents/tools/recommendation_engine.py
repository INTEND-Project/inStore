from datetime import date
from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field


class RecommendationEngineInput(BaseModel):
    objective: str = Field(description="Possible values are 'reduce_cost', 'reduce_latency', 'custom'")
    video_ids: list[str] = Field(
        description="""The list of video ID and source node pairs (e.g., "video123,EU_ORIGIN_COLD" ) that an action
            needs to be taken on. For system-wide objectives, all video IDs should be added here."""
    )
    cold_storage_euro_per_gb_per_month: str = Field(description="The cost of storage per GB per Month for cold storage")
    hot_storage_euro_per_gb_per_month: str = Field(description="The cost of storage per GB per Month for hot storage")
    cache_storage_euro_per_gb_per_month: str = Field(
        description="The cost of storage per GB per Month for cache storage"
    )
    devices: list[str] = Field(
        description="The current available nodes names, origin cold and hot storage should always be included."
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
        "This tool is responsible for providing the recommended commands according given inputs on the target environment and objectives."
    )
    args_schema: Optional[ArgsSchema] = RecommendationEngineInput

    def _run(
        self,
        objective: str,
        video_ids: list[str],
        cold_storage_euro_per_gb_per_month: str,
        hot_storage_euro_per_gb_per_month: str,
        cache_storage_euro_per_gb_per_month: str,
        devices: list[str],
        from_timestamp: str,
        to_timestamp: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        commands: list[str] = []
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
            for pair in video_ids:
                video_id, location = pair.split(",")
                if "cold" in location.lower():
                    commands.append(
                        str(
                            {
                                "date_time": _from,
                                "cmd": "MOVE",
                                "source": location,
                                "destination": hot_storage_devices[0],
                                "content_id": video_id,
                            }
                        )
                    )
                    if to_timestamp != "never":
                        commands.append(
                            str(
                                {
                                    "date_time": to,
                                    "cmd": "MOVE",
                                    "source": hot_storage_devices[0],
                                    "destination": location,
                                    "content_id": video_id,
                                }
                            )
                        )
                elif "cache" in location.lower():
                    continue
                elif "hot" in location.lower():
                    commands.append(
                        str(
                            {
                                "date_time": _from,
                                "cmd": "MOVE",
                                "source": location,
                                "destination": cache_devices[0],
                                "content_id": video_id,
                            }
                        )
                    )

                    if to_timestamp != "never":
                        commands.append(
                            str(
                                {
                                    "date_time": to,
                                    "cmd": "MOVE",
                                    "source": cold_storage_devices[0],
                                    "destination": location,
                                    "content_id": video_id,
                                }
                            )
                        )

        elif objective == "reduce_cost":
            for pair in video_ids:
                video_id, location = pair.split(",")
                if "cache" in location.lower():
                    commands.append(
                        str(
                            {
                                "date_time": _from,
                                "cmd": "MOVE",
                                "source": location,
                                "destination": hot_storage_devices[0],
                                "content_id": video_id,
                            }
                        )
                    )
                    if to_timestamp != "never":
                        commands.append(
                            str(
                                {
                                    "date_time": to,
                                    "cmd": "MOVE",
                                    "source": hot_storage_devices[0],
                                    "destination": location,
                                    "content_id": video_id,
                                }
                            )
                        )
                elif "cold" in location.lower():
                    continue
                elif "hot" in location.lower():
                    commands.append(
                        str(
                            {
                                "date_time": _from,
                                "cmd": "MOVE",
                                "source": location,
                                "destination": cold_storage_devices[0],
                                "content_id": video_id,
                            }
                        )
                    )

                    if to_timestamp != "never":
                        commands.append(
                            str(
                                {
                                    "date_time": to,
                                    "cmd": "MOVE",
                                    "source": cold_storage_devices[0],
                                    "destination": location,
                                    "content_id": video_id,
                                }
                            )
                        )
        return str({"commands": commands})
