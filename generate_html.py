#!/usr/bin/env python3
"""Generate the YouTube dashboard HTML from data.json."""

import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)


def pct(val, total):
    return round(val / total * 100) if total else 0


def bar_width(val, max_val):
    return round(val / max_val * 100) if max_val else 0


def like_rate(likes, views):
    return round(likes / views * 100, 1) if views else 0


def freshness_class(days):
    if days <= 14:
        return "fresh"
    elif days <= 30:
        return "stale"
    else:
        return "dormant"


def days_label(days):
    if days == 0:
        return "Today"
    elif days == 1:
        return "1 day ago"
    elif days < 7:
        return f"{days} days ago"
    elif days < 14:
        return "1 week ago"
    else:
        weeks = days // 7
        return f"{weeks} weeks ago"


channels = sorted(data["channels"], key=lambda c: c["views"], reverse=True)
max_views = channels[0]["views"] if channels else 1
total_views = data["totalViews"]

# Build pie chart degrees
pie_parts = []
cumulative = 0
colors = ["var(--gold)", "#b8860b", "var(--silver)", "#666", "#444"]
for i, ch in enumerate(channels):
    deg = round(ch["views"] / total_views * 360) if total_views else 0
    pie_parts.append(f"{colors[i]} {cumulative}deg {cumulative + deg}deg")
    cumulative += deg

pie_gradient = ", ".join(pie_parts)

# Legend
legend_html = ""
for i, ch in enumerate(channels):
    p = pct(ch["views"], total_views)
    short_name = ch["name"].split()[0] if len(ch["name"]) > 15 else ch["name"]
    legend_html += f'<div class="legend-item"><span class="legend-dot" style="background: {colors[i]};"></span> {short_name} ({p}%)</div>\n'

# Bar chart
bars_html = ""
for ch in channels:
    w = bar_width(ch["views"], max_views)
    v = f'{ch["views"]:,}'
    if w >= 25:
        bars_html += f'<div class="bar-row"><span class="bar-label">{ch["name"].split()[0]}</span><div class="bar-wrapper"><div class="bar" style="width: {w}%;">{v}</div></div></div>\n'
    else:
        bars_html += f'<div class="bar-row"><span class="bar-label">{ch["name"].split()[0]}</span><div class="bar-wrapper"><div class="bar" style="width: {max(w,2)}%;"></div><span class="bar-value">{v}</span></div></div>\n'

# Channel cards
channel_cards = ""
for ch in channels:
    per_video = int(ch["views"] / ch["videoCount"]) if ch["videoCount"] else 0
    prog = bar_width(ch["views"], max_views)
    fresh = freshness_class(ch["lastUploadDaysAgo"])
    upload_info = f'Last upload {ch["lastUploadFormatted"]}' if ch["lastUploadFormatted"] != "N/A" else "No uploads"
    channel_cards += f'''
    <div class="channel-card">
        <div class="channel-header">
            <div class="channel-avatar">{ch["icon"]}</div>
            <div class="channel-info">
                <h3>{ch["name"]}</h3>
                <p>Created {ch["created"]} • {ch["videoCount"]} videos • {upload_info}</p>
            </div>
        </div>
        <div class="channel-stats">
            <div class="channel-stat"><div class="channel-stat-value">{ch["subscribers"]}</div><div class="channel-stat-label">Subs</div></div>
            <div class="channel-stat"><div class="channel-stat-value">{ch["views"]:,}</div><div class="channel-stat-label">Views</div></div>
            <div class="channel-stat"><div class="channel-stat-value">{per_video}</div><div class="channel-stat-label">Per Video</div></div>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width: {prog}%;"></div></div>
    </div>'''

# Top videos
top_videos_html = ""
for v in data["topVideos"]:
    dur = v["durationFormatted"]
    comments_html = f'<span class="video-stat">💬 {v["comments"]}</span>' if v["comments"] > 0 else ""
    top_videos_html += f'''
    <div class="video-card">
        <div class="video-thumb">{v["channelIcon"]}</div>
        <div class="video-info">
            <div class="video-title">{v["title"]}</div>
            <div class="video-meta">{v["channelName"]} • {v["publishedFormatted"]} • {dur}</div>
            <div class="video-stats">
                <span class="video-stat views">👁 {v["views"]:,}</span>
                <span class="video-stat">👍 {v["likes"]}</span>
                {comments_html}
            </div>
        </div>
    </div>'''

# Engagement rows
engagement_html = ""
for v in data["engagement"]:
    lr = like_rate(v["likes"], v["views"])
    hl = ' highlight' if lr >= 3.0 else ''
    engagement_html += f'''
    <div class="engagement-row">
        <span class="title-col">{v["channelIcon"]} {v["title"][:40]}{"..." if len(v["title"]) > 40 else ""}</span>
        <span class="num-col">{v["views"]:,}</span>
        <span class="num-col{hl}">{v["likes"]}</span>
        <span class="num-col{hl}">{lr}%</span>
        <span class="num-col hide-mobile">{v["comments"]}</span>
    </div>'''

# Upload freshness
freshness_html = ""
for ch in sorted(channels, key=lambda c: c["lastUploadDaysAgo"]):
    days = ch["lastUploadDaysAgo"]
    fc = freshness_class(days)
    color_var = "var(--success)" if fc == "fresh" else ("var(--warning, #ff9500)" if fc == "stale" else "var(--danger)")
    bg = "rgba(52,199,89,0.05)" if fc == "fresh" else ("rgba(255,149,0,0.05)" if fc == "stale" else "rgba(255,59,48,0.05)")
    freshness_html += f'''
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: {bg}; border-radius: 8px; border-left: 3px solid {color_var};">
        <span style="font-size: 0.8125rem;">{ch["icon"]} {ch["name"].split()[0]}</span>
        <span style="font-size: 0.8125rem; color: {color_var}; font-weight: 600;">{ch["lastUploadFormatted"]} — {days_label(days)}</span>
    </div>'''

# Recent uploads
recent_html = ""
for v in data["recentUploads"]:
    lr = like_rate(v["likes"], v["views"])
    lr_html = f'<span class="video-stat" style="color: var(--success);">{lr}% like rate</span>' if v["views"] >= 20 and lr >= 3.0 else ""
    if v["daysAgo"] <= 2 and v["views"] < 10:
        lr_html = '<span class="video-stat" style="color: var(--text-tertiary);">Just uploaded</span>'
    recent_html += f'''
    <div class="video-card">
        <div class="video-thumb">{v["channelIcon"]}</div>
        <div class="video-info">
            <div class="video-title">{v["title"]}</div>
            <div class="video-meta">{v["channelName"]} • {v["publishedFormatted"]} • {v["durationFormatted"]}</div>
            <div class="video-stats">
                <span class="video-stat views">👁 {v["views"]:,}</span>
                <span class="video-stat">👍 {v["likes"]}</span>
                {lr_html}
            </div>
        </div>
    </div>'''

# Engagement totals
avg_like_rate = like_rate(data["totalLikes"], total_views)
likes_per_vid = round(data["totalLikes"] / data["totalVideos"], 1) if data["totalVideos"] else 0

# Shorts data
shorts = data["shorts"]
longform = data["longform"]

# Channel links
links_html = ""
for ch in channels:
    links_html += f'''
    <tr>
        <td><span class="channel-name"><span class="channel-icon-sm">{ch["icon"]}</span> {ch["name"]}</span></td>
        <td><a href="https://youtube.com/channel/{ch["id"]}" target="_blank">Open ↗</a></td>
        <td><code>{ch["id"]}</code></td>
    </tr>'''

# Insights (auto-generated)
top_ch = channels[0]
fastest_growing = max(channels, key=lambda c: c["subscribers"])
insights = []
insights.append(f'<li class="insight-item"><span class="insight-icon">🏆</span><span class="insight-text"><strong>{top_ch["name"]}</strong> leads with {pct(top_ch["views"], total_views)}% of all views ({top_ch["views"]:,})</span></li>')

if fastest_growing["id"] != top_ch["id"]:
    insights.append(f'<li class="insight-item"><span class="insight-icon">📈</span><span class="insight-text"><strong>{fastest_growing["name"]}</strong> has the most subscribers ({fastest_growing["subscribers"]}) — highest sub conversion</span></li>')

if shorts["count"] > 0 and longform["count"] > 0 and longform["avgViews"] > 0:
    ratio = round(shorts["avgViews"] / longform["avgViews"], 1)
    insights.append(f'<li class="insight-item"><span class="insight-icon">📱</span><span class="insight-text"><strong>Shorts outperform long-form by {ratio}x</strong> ({shorts["avgViews"]} vs {longform["avgViews"]} avg views)</span></li>')

# Find best engagement video
if data["engagement"]:
    best_eng = data["engagement"][0]
    best_lr = like_rate(best_eng["likes"], best_eng["views"])
    insights.append(f'<li class="insight-item"><span class="insight-icon">🧠</span><span class="insight-text"><strong>Top engagement:</strong> "{best_eng["title"][:40]}" — {best_lr}% like rate</span></li>')

dormant = [c for c in channels if c["lastUploadDaysAgo"] > 60]
if dormant:
    names = ", ".join(c["name"].split()[0] for c in dormant)
    insights.append(f'<li class="insight-item"><span class="insight-icon">⚠️</span><span class="insight-text"><strong>{names}</strong> — no uploads in 60+ days, consider refreshing</span></li>')

active = [c for c in channels if c["lastUploadDaysAgo"] <= 14]
if active:
    names = ", ".join(c["name"].split()[0] for c in active)
    insights.append(f'<li class="insight-item"><span class="insight-icon">✅</span><span class="insight-text"><strong>Active channels:</strong> {names} — uploaded in the last 2 weeks</span></li>')

insights_html = "\n".join(insights)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Analytics — IPAI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #2d2d2d;
            --bg-secondary: #3a3a3a;
            --silver: #a8a8a8;
            --silver-light: #c5c5c5;
            --gold: #d4af37;
            --gold-light: #e8c547;
            --gold-bright: #f5d742;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-tertiary: rgba(255, 255, 255, 0.5);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --success: #34c759;
            --danger: #ff3b30;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary); min-height: 100vh; color: var(--text-primary);
            -webkit-font-smoothing: antialiased;
        }}
        .bg-gradient {{
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at 20% 0%, rgba(255,0,0,0.05) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 100%, rgba(212,175,55,0.06) 0%, transparent 50%),
                        var(--bg-primary);
            z-index: -1;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 48px 24px; }}
        header {{ text-align: center; margin-bottom: 48px; }}
        h1 {{
            font-size: 2.25rem; font-weight: 700; letter-spacing: -0.03em;
            background: linear-gradient(180deg, var(--silver-light) 0%, var(--gold) 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;
        }}
        .subtitle {{ font-size: 1rem; color: var(--text-secondary); margin-bottom: 8px; }}
        .updated {{ font-size: 0.8125rem; color: var(--text-tertiary); }}
        .auto-badge {{ display: inline-block; font-size: 0.625rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; padding: 2px 8px; border-radius: 4px; background: rgba(52,199,89,0.15); color: var(--success); margin-left: 8px; vertical-align: middle; }}
        .stats-bar {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px; margin-bottom: 40px;
        }}
        .stat-box {{
            background: var(--glass-bg); backdrop-filter: blur(20px); border-radius: 14px;
            padding: 20px; text-align: center; border: 1px solid var(--glass-border); transition: all 0.25s ease;
        }}
        .stat-box:hover {{ border-color: rgba(212,175,55,0.3); transform: translateY(-2px); }}
        .stat-box.highlight {{ border-color: rgba(212,175,55,0.25); }}
        .stat-value {{
            font-size: 1.75rem; font-weight: 700;
            background: linear-gradient(180deg, var(--silver) 0%, var(--gold-light) 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.02em;
        }}
        .stat-label {{ font-size: 0.6875rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
        @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        .card {{
            background: var(--glass-bg); backdrop-filter: blur(20px); border-radius: 16px;
            padding: 24px; border: 1px solid var(--glass-border); margin-bottom: 16px;
        }}
        .card-header {{
            display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
            padding-bottom: 16px; border-bottom: 1px solid var(--glass-border);
        }}
        .card-icon {{ font-size: 1.25rem; }}
        .card-title {{ font-size: 1rem; font-weight: 600; letter-spacing: -0.01em; }}
        .card-badge {{ margin-left: auto; font-size: 0.625rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; padding: 3px 8px; border-radius: 6px; background: rgba(212,175,55,0.15); color: var(--gold); }}
        .bar-chart {{ display: flex; flex-direction: column; gap: 10px; }}
        .bar-row {{ display: flex; align-items: center; gap: 12px; }}
        .bar-label {{ width: 100px; font-size: 0.8125rem; color: var(--text-secondary); text-align: right; }}
        .bar-wrapper {{ flex: 1; height: 28px; background: rgba(255,255,255,0.03); border-radius: 8px; overflow: hidden; position: relative; }}
        .bar {{ height: 100%; background: linear-gradient(90deg, var(--gold) 0%, var(--gold-bright) 100%); border-radius: 8px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-size: 0.75rem; font-weight: 600; color: var(--bg-primary); }}
        .bar-value {{ position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 0.8125rem; color: var(--text-secondary); }}
        .pie-container {{ display: flex; align-items: center; gap: 32px; justify-content: center; flex-wrap: wrap; }}
        .pie-chart {{ width: 160px; height: 160px; border-radius: 50%; background: conic-gradient({pie_gradient}); position: relative; }}
        .pie-chart::before {{ content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90px; height: 90px; background: var(--bg-primary); border-radius: 50%; }}
        .pie-center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }}
        .pie-value {{ font-size: 1.375rem; font-weight: 700; color: var(--gold); }}
        .pie-label {{ font-size: 0.6875rem; color: var(--text-tertiary); }}
        .legend {{ display: flex; flex-direction: column; gap: 8px; }}
        .legend-item {{ display: flex; align-items: center; gap: 10px; font-size: 0.8125rem; color: var(--text-secondary); }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 3px; }}
        .channel-card {{ background: rgba(255,255,255,0.02); border-radius: 14px; padding: 20px; margin-bottom: 12px; border: 1px solid transparent; transition: all 0.25s ease; }}
        .channel-card:hover {{ border-color: rgba(212,175,55,0.2); background: rgba(255,255,255,0.04); }}
        .channel-card:last-child {{ margin-bottom: 0; }}
        .channel-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }}
        .channel-avatar {{ width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, var(--gold) 0%, var(--silver) 100%); display: flex; align-items: center; justify-content: center; font-size: 1.125rem; }}
        .channel-info h3 {{ font-size: 1rem; font-weight: 600; margin-bottom: 2px; }}
        .channel-info p {{ font-size: 0.75rem; color: var(--text-tertiary); }}
        .channel-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
        .channel-stat {{ text-align: center; padding: 12px 8px; background: rgba(255,255,255,0.02); border-radius: 10px; }}
        .channel-stat-value {{ font-size: 1.125rem; font-weight: 700; color: var(--gold); }}
        .channel-stat-label {{ font-size: 0.625rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.03em; margin-top: 2px; }}
        .progress-bar {{ height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; margin-top: 12px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, var(--gold), var(--gold-bright)); border-radius: 2px; }}
        .video-card {{ display: flex; gap: 14px; padding: 14px; background: rgba(255,255,255,0.02); border-radius: 12px; margin-bottom: 10px; transition: all 0.2s ease; }}
        .video-card:hover {{ background: rgba(255,255,255,0.05); }}
        .video-card:last-child {{ margin-bottom: 0; }}
        .video-thumb {{ width: 72px; height: 44px; background: linear-gradient(135deg, var(--gold), var(--silver)); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }}
        .video-info {{ flex: 1; min-width: 0; }}
        .video-title {{ font-size: 0.875rem; font-weight: 500; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .video-meta {{ font-size: 0.6875rem; color: var(--text-tertiary); }}
        .video-stats {{ display: flex; gap: 12px; margin-top: 6px; }}
        .video-stat {{ font-size: 0.75rem; color: var(--text-tertiary); display: flex; align-items: center; gap: 4px; }}
        .video-stat.views {{ color: var(--gold); font-weight: 600; }}
        .insight-list {{ list-style: none; }}
        .insight-item {{ display: flex; gap: 12px; padding: 14px 0; border-bottom: 1px solid var(--glass-border); }}
        .insight-item:last-child {{ border-bottom: none; }}
        .insight-icon {{ font-size: 1.125rem; flex-shrink: 0; }}
        .insight-text {{ font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; }}
        .insight-text strong {{ color: var(--gold); }}
        .engagement-row {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 8px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.8125rem; align-items: center; }}
        .engagement-row.header {{ font-size: 0.6875rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; border-bottom: 1px solid var(--glass-border); }}
        .engagement-row .title-col {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-secondary); }}
        .engagement-row .num-col {{ text-align: right; color: var(--text-tertiary); }}
        .engagement-row .num-col.highlight {{ color: var(--gold); font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; font-size: 0.6875rem; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; padding: 12px 8px; border-bottom: 1px solid var(--glass-border); }}
        td {{ padding: 14px 8px; font-size: 0.875rem; border-bottom: 1px solid rgba(255,255,255,0.03); }}
        tr:hover {{ background: rgba(255,255,255,0.02); }}
        .channel-name {{ display: flex; align-items: center; gap: 10px; }}
        .channel-icon-sm {{ width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, var(--gold), var(--silver)); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; }}
        a {{ color: var(--gold); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        code {{ font-family: 'SF Mono', monospace; font-size: 0.6875rem; color: var(--text-tertiary); }}
        footer {{ text-align: center; margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--glass-border); font-size: 0.8125rem; color: var(--text-tertiary); }}
        @media (max-width: 768px) {{
            .container {{ padding: 32px 16px; }}
            h1 {{ font-size: 1.75rem; }}
            .engagement-row {{ grid-template-columns: 2fr 1fr 1fr 1fr; }}
            .engagement-row .hide-mobile {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="bg-gradient"></div>
    <div class="container">
        <header>
            <h1>YouTube Analytics</h1>
            <p class="subtitle">Video Content Performance — Inception Point AI</p>
            <p class="updated">Last updated: {data["updated"]} <span class="auto-badge">Auto-Updated</span></p>
        </header>

        <div class="stats-bar">
            <div class="stat-box highlight"><div class="stat-value">{len(channels)}</div><div class="stat-label">Channels</div></div>
            <div class="stat-box"><div class="stat-value">{data["totalSubs"]}</div><div class="stat-label">Subscribers</div></div>
            <div class="stat-box highlight"><div class="stat-value">{data["totalViews"]:,}</div><div class="stat-label">Total Views</div></div>
            <div class="stat-box"><div class="stat-value">{data["totalVideos"]}</div><div class="stat-label">Videos</div></div>
            <div class="stat-box"><div class="stat-value">{data["avgViews"]}</div><div class="stat-label">Avg Views</div></div>
            <div class="stat-box"><div class="stat-value">{data["channelAge"]}</div><div class="stat-label">Age</div></div>
        </div>

        <div class="grid-2">
            <div class="card">
                <div class="card-header"><span class="card-icon">📊</span><span class="card-title">Views by Channel</span></div>
                <div class="bar-chart">{bars_html}</div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-icon">🥧</span><span class="card-title">View Distribution</span></div>
                <div class="pie-container">
                    <div class="pie-chart"><div class="pie-center"><div class="pie-value">{data["totalViews"]:,}</div><div class="pie-label">views</div></div></div>
                    <div class="legend">{legend_html}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><span class="card-icon">📈</span><span class="card-title">Channel Performance</span></div>
            {channel_cards}
        </div>

        <div class="grid-2">
            <div class="card">
                <div class="card-header"><span class="card-icon">🔥</span><span class="card-title">Top Videos (All Time)</span></div>
                {top_videos_html}
            </div>
            <div class="card">
                <div class="card-header"><span class="card-icon">💡</span><span class="card-title">Insights</span><span class="card-badge">Auto-Generated</span></div>
                <ul class="insight-list">{insights_html}</ul>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><span class="card-icon">💬</span><span class="card-title">Engagement Deep Dive</span></div>
            <div class="engagement-row header">
                <span>Video</span><span style="text-align:right;">Views</span><span style="text-align:right;">Likes</span><span style="text-align:right;">Like Rate</span><span style="text-align:right;" class="hide-mobile">Comments</span>
            </div>
            {engagement_html}
            <div style="margin-top: 20px; padding: 16px; background: rgba(255,255,255,0.02); border-radius: 12px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; text-align: center;">
                    <div><div style="font-size: 1.5rem; font-weight: 700; color: var(--gold);">{data["totalLikes"]}</div><div style="font-size: 0.625rem; color: var(--text-tertiary); text-transform: uppercase;">Total Likes</div></div>
                    <div><div style="font-size: 1.5rem; font-weight: 700; color: var(--gold);">{data["totalComments"]}</div><div style="font-size: 0.625rem; color: var(--text-tertiary); text-transform: uppercase;">Total Comments</div></div>
                    <div><div style="font-size: 1.5rem; font-weight: 700; color: var(--gold);">{avg_like_rate}%</div><div style="font-size: 0.625rem; color: var(--text-tertiary); text-transform: uppercase;">Avg Like Rate</div></div>
                    <div><div style="font-size: 1.5rem; font-weight: 700; color: var(--gold);">{likes_per_vid}</div><div style="font-size: 0.625rem; color: var(--text-tertiary); text-transform: uppercase;">Likes/Video</div></div>
                </div>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <div class="card-header"><span class="card-icon">⏱️</span><span class="card-title">Shorts vs Long-Form</span></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
                    <div style="padding: 16px; background: rgba(212,175,55,0.05); border-radius: 12px; border: 1px solid rgba(212,175,55,0.15); text-align: center;">
                        <div style="font-size: 0.6875rem; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 8px;">📱 Shorts (≤60s)</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--gold);">{shorts["count"]}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">videos</div>
                        <div style="margin-top: 8px; font-size: 0.875rem; color: var(--success);">Avg {shorts["avgViews"]} views</div>
                    </div>
                    <div style="padding: 16px; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px solid var(--glass-border); text-align: center;">
                        <div style="font-size: 0.6875rem; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 8px;">🎬 Long-Form (>60s)</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--silver);">{longform["count"]}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">videos</div>
                        <div style="margin-top: 8px; font-size: 0.875rem; color: var(--text-tertiary);">Avg {longform["avgViews"]} views</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header"><span class="card-icon">📅</span><span class="card-title">Upload Freshness</span></div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    {freshness_html}
                </div>
            </div>
        </div>

        {"" if not recent_html else f"""
        <div class="card">
            <div class="card-header"><span class="card-icon">🆕</span><span class="card-title">Recent Uploads (Last 30 Days)</span></div>
            {recent_html}
        </div>
        """}

        <div class="card">
            <div class="card-header"><span class="card-icon">🔗</span><span class="card-title">Channel Links</span></div>
            <table><thead><tr><th>Channel</th><th>Link</th><th>ID</th></tr></thead><tbody>{links_html}</tbody></table>
        </div>

        <footer>Inception Point AI • YouTube Analytics • Auto-updated every 6 hours</footer>
    </div>
</body>
</html>'''

print(html)
