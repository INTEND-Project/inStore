import csv
import os
from typing import Optional

from langchain.tools import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field


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
                    print(e)
                    failed += 1

            return f"Successfully moved {succeeded} videos, failed to move {failed} videos... skipping"

    def _process_row(self, row):
        """Process a single row from the CSV file."""
        if len(row) < 3:
            raise Exception("Invalid row (insufficient columns)")

        video_id = row[0].strip()
        current_location = row[1].strip()
        destination_node = row[2].strip()

        # TODO: Use MOG API to move video_id to destination_node
        print(video_id, current_location, destination_node)

    async def _arun(self, csv_file_path: str) -> str:
        """Async version of the tool."""
        return self._run(csv_file_path)
