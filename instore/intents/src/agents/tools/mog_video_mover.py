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

            succeeded = 0
            failed = 0
            for row in reader:
                try:
                    self._process_row(row)
                    succeeded += 1
                except Exception as e:
                    pretty_print(e, "Tool Message (Video Mover)")
                    failed += 1

        pretty_print(
            f"Successfully moved {succeeded} videos, failed to move {failed} videos... skipping",
            title="Tool Message (Video Mover)",
        )
        return f"Successfully moved {succeeded} videos, failed to move {failed} videos... skipping"

    def _process_row(self, row):
        """Process a single row from the CSV file."""
        if len(row) < 2:
            raise Exception("Invalid row (insufficient columns)")

        video_id = row[0].strip()
        source_node = row[1].strip()
        destination_node = row[2].strip()

        api_base_url = "http://10.13.14.1:30070"
        should_purge = destination_node is None or destination_node == ""
        is_source_origin = "hot" in source_node or "cold" in source_node
        is_destination_origin = "hot" in destination_node or "cold" in destination_node

        if should_purge:  # purge
            requests.post(
                f"{api_base_url}/files/purge",
                {"file": video_id, "region": source_node},
                timeout=10,
            )
        elif is_source_origin and is_destination_origin:  # move
            requests.post(
                f"{api_base_url}/files/move",
                {"file": video_id, "destination": destination_node, "source": source_node},
                timeout=10,
            )
        elif is_source_origin:  # copy
            requests.get(
                f"{api_base_url}/files/copy",
                {"region": destination_node, "file": video_id},
                timeout=10,
            )
        else:
            raise Exception("Unknown movement case")

    async def _arun(self, csv_file_path: str) -> str:
        """Async version of the tool."""
        return self._run(csv_file_path)
