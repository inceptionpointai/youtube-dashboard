#!/usr/bin/env python3
"""Fetch YouTube channel and video data via Data API v3."""

import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

API_KEY = sys.argv[1]
BASE = "https://www.googleapis.com/youtube/v3"

CHANNELS = {
    "UCcXcEDIls_yg_B48rtXGmDg": {"name": "DIY HOME & GARDEN", "icon": "🏠", "created": "Dec 28"},
    "UC4whjCHC9UbSH5pAVpShL3w": {"name": "History You Never Learned", "icon": "📚", "created": "Dec 29"},
    "UCy11lIokKOGdWNuMP2XUacA": {"name": "Everyday Food and Living", "icon": "🍳", "created": "Dec 28"},
    "UCpeVZ34xMRpaAd1zpjGMh7Q": {"name": "TECH EXPLAINED", "icon": "💻", "created": "Dec 29"},
    "UCxShkKdP9HOVJc4fV5RZclA": {"name": "Biography Unlimited", "icon": "👤", "created": "Dec 29"},
}


def api_get(endpoint, params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def fetch_channel_stats():
    ids = ",".join(CHANNELS.keys())
    data = api_get("channels", {"part": "statistics,snippet", "id": ids})
    results = {}
    for item in data.get("items", []):
        cid = item["id"]
        stats = item["statistics"]
        results[cid] = {
            **CHANNELS[cid],
            "id": cid,
            "subscribers": int(stats.get("subscriberCount", 0)),
            "views": int(stats.get("viewCount", 0)),
            "videoCount": int(stats.get("videoCount", 0)),
        }
    return results


def fetch_channel_videos(channel_id, max_results=15):
    # Get video IDs
    search = api_get("search", {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "maxResults": max_results,
        "type": "video",
    })
    video_ids = [item["id"]["videoId"] for item in search.get("items", []) if "videoId" in item.get("id", {})]
    if not video_ids:
        return []

    # Get detailed stats
    details = api_get("videos", {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(video_ids),
    })

    videos = []
    for item in details.get("items", []):
        stats = item["statistics"]
        duration = item["contentDetails"]["duration"]  # PT#M#S format
        published = item["snippet"]["publishedAt"]

        # Parse duration
        dur_str = duration.replace("PT", "")
        seconds = 0
        if "H" in dur_str:
            h, dur_str = dur_str.split("H")
            seconds += int(h) * 3600
        if "M" in dur_str:
            m, dur_str = dur_str.split("M")
            seconds += int(m) * 60
        if "S" in dur_str:
            s = dur_str.replace("S", "")
            seconds += int(s)

        pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_ago = (now - pub_date).days

        videos.append({
            "id": item["id"],
            "title": item["snippet"]["title"],
            "published": published,
            "publishedFormatted": pub_date.strftime("%b %d"),
            "daysAgo": days_ago,
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "durationSeconds": seconds,
            "durationFormatted": format_duration(seconds),
            "isShort": seconds <= 60,
            "channelId": channel_id,
        })

    return videos


def format_duration(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s" if s else f"{m}m"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


def main():
    channels = fetch_channel_stats()

    all_videos = []
    for cid in CHANNELS:
        vids = fetch_channel_videos(cid)
        for v in vids:
            v["channelName"] = channels[cid]["name"]
            v["channelIcon"] = channels[cid]["icon"]
        channels[cid]["videos"] = vids
        channels[cid]["lastUpload"] = vids[0]["published"] if vids else None
        channels[cid]["lastUploadFormatted"] = vids[0]["publishedFormatted"] if vids else "N/A"
        channels[cid]["lastUploadDaysAgo"] = vids[0]["daysAgo"] if vids else 999
        all_videos.extend(vids)

    # Compute totals
    total_views = sum(c["views"] for c in channels.values())
    total_subs = sum(c["subscribers"] for c in channels.values())
    total_videos = sum(c["videoCount"] for c in channels.values())
    total_likes = sum(v["likes"] for v in all_videos)
    total_comments = sum(v["comments"] for v in all_videos)

    # Top videos
    top_videos = sorted(all_videos, key=lambda v: v["views"], reverse=True)[:8]

    # Recent uploads (last 30 days)
    recent = [v for v in all_videos if v["daysAgo"] <= 30]
    recent.sort(key=lambda v: v["published"], reverse=True)

    # Shorts vs long-form
    shorts = [v for v in all_videos if v["isShort"]]
    longform = [v for v in all_videos if not v["isShort"]]
    shorts_avg = int(sum(v["views"] for v in shorts) / len(shorts)) if shorts else 0
    longform_avg = int(sum(v["views"] for v in longform) / len(longform)) if longform else 0

    # Engagement leaders
    engagement = sorted(
        [v for v in all_videos if v["views"] >= 50],
        key=lambda v: v["likes"] / max(v["views"], 1),
        reverse=True,
    )[:8]

    # Channel age
    from datetime import datetime as dt
    start = dt(2025, 12, 28, tzinfo=timezone.utc)
    weeks = (datetime.now(timezone.utc) - start).days // 7

    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y @ %I:%M %p UTC")

    output = {
        "updated": now_str,
        "updatedISO": datetime.now(timezone.utc).isoformat(),
        "totalViews": total_views,
        "totalSubs": total_subs,
        "totalVideos": total_videos,
        "totalLikes": total_likes,
        "totalComments": total_comments,
        "avgViews": int(total_views / total_videos) if total_videos else 0,
        "channelAge": f"~{weeks}w",
        "channels": list(channels.values()),
        "topVideos": top_videos,
        "recentUploads": recent[:8],
        "engagement": engagement,
        "shorts": {
            "count": len(shorts),
            "totalViews": sum(v["views"] for v in shorts),
            "avgViews": shorts_avg,
        },
        "longform": {
            "count": len(longform),
            "totalViews": sum(v["views"] for v in longform),
            "avgViews": longform_avg,
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
