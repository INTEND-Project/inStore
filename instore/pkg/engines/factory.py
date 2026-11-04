import os

from pkg.config import ComponentInfo
from pkg.interfaces import RecommendationEngine

from .mog_cdn import MogCdnEngine


def engine_factory(info: ComponentInfo, dry_run: bool) -> RecommendationEngine:
    """Creates the recommendation engine selected in the use_case section of the config file."""
    if info.provider == "mog_cdn":
        # In a dry run, plan against mock videos instead of the MOG API
        return MogCdnEngine(api_url=os.environ.get("MOG_API_URL"), use_mock_videos=dry_run)
    raise ValueError(f"Unknown recommendation engine {info.provider}")
