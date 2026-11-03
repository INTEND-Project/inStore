import hashlib
from typing import Dict, List

import requests

from pkg.interfaces import Action

REGION_CAPACITY_MB: Dict[str, int] = {
    "us-east-1": 50_000,       # 50 GB
    "eu-central-1": 30_000,    # 30 GB
    "br-southeast-1": 20_000,  # 20 GB
}

REDUCE_LATENCY = 'REDUCE_LATENCY'
REDUCE_COST = 'REDUCE_COST'

def fake_size_mb(video_key: str) -> int:
    """
    Deterministic fake size from key.
    Range: 200MB .. 3500MB
    """
    h = hashlib.md5(video_key.encode("utf-8")).hexdigest()
    x = int(h[:8], 16)
    return 200 + (x % 3301)

def fetch_all_videos(base_url: str) -> List[dict]:
    page = 1
    videos: List[dict] = []

    while True:
        resp = requests.get(base_url, params={"page": page}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        videos.extend(payload.get("data", []))

        next_page = payload.get("nextPage")
        if not next_page:
            break
        page = next_page

    return videos

def destination_origin_tier(mode: str, overall_pred: int, total_views: int) -> str:
    if mode == REDUCE_LATENCY:
        return "hot" if overall_pred >= 3 else "cold"

    if mode == REDUCE_COST:
        if overall_pred >= 4:
            return "hot"
        if overall_pred <= 2:
            return "cold"
        return "hot" if total_views >= 300 else "cold"

    raise ValueError(f"Unknown mode: {mode}")

def copy_to_cache(mode: str, region_pred: int, region_views: int, size_mb: int) -> bool:
    if mode == REDUCE_LATENCY:
        return region_pred >= 3

    if mode == REDUCE_COST:
        if region_pred >= 4:
            return True
        if region_pred == 3 and region_views >= 50 and size_mb <= 1500:
            return True
        return False

    raise ValueError(f"Unknown mode: {mode}")

def plan(mode: str, videos: List[dict]) -> List[Action]:
    """Returns the actions that place the videos according to the mode: tier moves first, then cache purges, then cache copies."""

    size_by_key: Dict[str, int] = {v["key"]: fake_size_mb(v["key"]) for v in videos}
    
    actions: List[Action] = []
    purge_actions: List[Action] = []
    copy_candidates: List[Action] = []

    for video in videos:
        videoid = video['videoid']
        key = video['key']
        overall_prediction = video['prediction']
        total_views = video['views']
        storage = video['storage']['name']
        
        # print(f"VideoID: {videoid}\nKey: {key}\nOverall Predication: {overall_prediction}\nStorage: {storage}")
        
        destination = destination_origin_tier(mode=mode, overall_pred=overall_prediction, total_views=total_views)
        
        if storage != destination:
            action = Action(type="move", content_id=key, source=storage, destination=destination)
            actions.append(action)
             
        for cache in video['edgeNodes']:
            region = cache['region']
            cache_prediction = cache['prediction']
            region_views = cache['views']
            is_cached = cache['isCached']
            
            # print(f"Region: {region}\nPrediction: {cache_prediction}\nIsCached: {is_cached}")
            
            wants_cache = copy_to_cache(mode=mode, region_pred=cache_prediction, region_views=region_views, size_mb=size_by_key[key])

            if is_cached:
                if not wants_cache:
                    action = Action(type="purge", content_id=key, source=region)
                    purge_actions.append(action)
            elif wants_cache:
                action = Action(type="copy", content_id=key, source=destination, destination=region)
                copy_candidates.append(action)
                
        # print("\n")
                
    actions.extend(purge_actions)
    actions.extend(copy_candidates)
    
    return actions
