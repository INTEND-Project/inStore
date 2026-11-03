import os
from typing import Optional

from langchain.tools import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from pkg.interfaces import Executor
from pkg.utils.pretty_print import pretty_print

from .actions_csv import read_actions_csv


class VideoMoveInput(BaseModel):
    csv_file_path: str = Field(
        description="Path to the CSV file containing video files, their current lcoations, and their destination locations"
    )


class VideoMover(BaseTool):
    name: str = "video_mover"

    description: str = "Moves video files to specified locations based on a CSV mapping file"

    args_schema: Optional[ArgsSchema] = VideoMoveInput

    executor: Executor

    def _run(self, csv_file_path: str) -> str:

        # Validate CSV file exists
        if not os.path.exists(csv_file_path):
            return f"Error: CSV file {csv_file_path} not found"

        results = self.executor.execute(read_actions_csv(csv_file_path))

        # Each result is one action (move, copy, or purge) on one video, a video can appear in several actions
        succeeded = {"move": 0, "copy": 0, "purge": 0}
        failed = 0
        videos = set()
        for r in results:
            if r.ok:
                succeeded[r.action.type] += 1
                videos.add(r.action.content_id)
            else:
                pretty_print(f"{r.action}: {r.error}", "Tool Message (Video Mover)")
                failed += 1

        summary = (
            f"Successfully completed {sum(succeeded.values())} actions on {len(videos)} videos "
            f"({succeeded['move']} moves, {succeeded['copy']} copies, {succeeded['purge']} purges), "
            f"{failed} actions failed"
        )
        if self.executor.dry_run:
            summary += " (dry run: simulated, no changes were made to the MOG environment)"

        pretty_print(summary, title="Tool Message (Video Mover)")
        return summary

    async def _arun(self, csv_file_path: str) -> str:
        """Async version of the tool."""
        return self._run(csv_file_path)
