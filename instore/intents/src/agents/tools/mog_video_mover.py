import csv
import os
from typing import Optional

import requests
from langchain.tools import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from pkg.utils.pretty_print import pretty_print


class VideoMoveInput(BaseModel):
    csv_file_path: str = Field(
        description="Path to the CSV file containing video files, their current lcoations, and their destination locations"
    )


class VideoMover(BaseTool):
    name: str = "video_mover"

    description: str = "Moves video files to specified locations based on a CSV mapping file"

    args_schema: Optional[ArgsSchema] = VideoMoveInput

    def _run(self, csv_file_path: str) -> str:

        # Validate CSV file exists
        if not os.path.exists(csv_file_path):
            return f"Error: CSV file {csv_file_path} not found"

        with open(csv_file_path, "r", newline="", encoding="utf-8") as csvfile:

            reader = csv.reader(csvfile, delimiter=",")

            # Each row is one action (move, copy, or purge) on one video, a video can appear in several rows
            succeeded = {"move": 0, "copy": 0, "purge": 0}
            failed = 0
            videos = set()
            for row in reader:
                try:
                    action = self._process_row(row)
                    succeeded[action] += 1
                    videos.add(row[0].strip())
                except Exception as e:
                    pretty_print(e, "Tool Message (Video Mover)")
                    failed += 1

        summary = (
            f"Successfully completed {sum(succeeded.values())} actions on {len(videos)} videos "
            f"({succeeded['move']} moves, {succeeded['copy']} copies, {succeeded['purge']} purges), "
            f"{failed} actions failed"
        )
        if self._is_dry_run():
            summary += " (dry run: simulated, no changes were made to the MOG environment)"

        pretty_print(summary, title="Tool Message (Video Mover)")
        return summary

    def _is_dry_run(self) -> bool:
        return os.environ.get("MOG_DRY_RUN", "").lower() in ("true", "1")

    def _process_row(self, row) -> str:
        """Process a single row from the CSV file and return its action (move, copy, or purge)."""
        if len(row) < 2:
            raise Exception("Invalid row (insufficient columns)")

        video_id = row[0].strip()
        source_node = row[1].strip()
        destination_node = row[2].strip()

        api_base_url = os.environ.get("MOG_API_URL")
        should_purge = destination_node is None or destination_node == ""
        is_source_origin = "hot" in source_node or "cold" in source_node
        is_destination_origin = "hot" in destination_node or "cold" in destination_node

        if should_purge:
            action = "purge"
        elif is_source_origin and is_destination_origin:
            action = "move"
        elif is_source_origin:
            action = "copy"
        else:
            raise Exception("Unknown movement case")

        if self._is_dry_run():
            print(f"[DRY RUN] {action} {video_id}: {source_node} -> {destination_node or '(purged)'}")
            return action

        if action == "purge":
            requests.post(
                f"{api_base_url}/files/purge",
                {"file": video_id, "region": source_node},
                timeout=10,
            )
        elif action == "move":
            requests.post(
                f"{api_base_url}/files/move",
                {"file": video_id, "destination": destination_node, "source": source_node},
                timeout=10,
            )
        elif action == "copy":
            requests.get(
                f"{api_base_url}/files/copy",
                {"region": destination_node, "file": video_id},
                timeout=10,
            )

        return action

    async def _arun(self, csv_file_path: str) -> str:
        """Async version of the tool."""
        return self._run(csv_file_path)
