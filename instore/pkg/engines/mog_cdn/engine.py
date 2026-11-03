import json
import os
from typing import Optional

from pkg.interfaces import Action, Objective, RecommendationEngine
from pkg.utils.pretty_print import pretty_print

from .planner import REDUCE_COST, REDUCE_LATENCY, fetch_all_videos, plan

MOCK_VIDEOS_PATH = os.path.join(os.path.dirname(__file__), "mock_videos.json")


class MogCdnEngine(RecommendationEngine):
    """Places videos across the MOG origin tiers (hot, cold) and regional caches."""

    def __init__(self, api_url: Optional[str] = None, use_mock_videos: bool = False):
        self.api_url = api_url
        self.use_mock_videos = use_mock_videos
        self.objectives = [
            Objective(
                name=REDUCE_COST,
                description="Reduce storage and delivery costs by keeping fewer videos in hot storage and caches",
                conflicts_with=[REDUCE_LATENCY],
            ),
            Objective(
                name=REDUCE_LATENCY,
                description="Reduce viewer latency by keeping popular videos in hot storage and regional caches",
                conflicts_with=[REDUCE_COST],
            ),
        ]

    def recommend(self, objective: str, params: Optional[dict] = None) -> list[Action]:
        self.get_objective(objective)
        return plan(mode=objective, videos=self._videos())

    def _videos(self) -> list[dict]:
        if self.use_mock_videos:
            pretty_print(f"[DRY RUN] Using mock videos from '{MOCK_VIDEOS_PATH}'", "MOG CDN Engine")
            with open(MOCK_VIDEOS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        if not self.api_url:
            raise ValueError("MOG_API_URL is not set")
        return fetch_all_videos(f"{self.api_url}/videos")
