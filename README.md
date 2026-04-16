# YouTube Analytics Dashboard — IPAI

Auto-updating YouTube analytics dashboard for Inception Point AI's 5 YouTube channels.

**Live:** https://inceptionpointai.github.io/youtube-dashboard/

## How It Works

1. `fetch_data.py` pulls live stats from YouTube Data API v3
2. `generate_html.py` renders the dashboard HTML from the data
3. `update.sh` orchestrates both steps
4. A cron job runs every 6 hours, commits & pushes updates
5. GitHub Pages serves the latest `index.html`

## Channels Tracked

- 🏠 DIY HOME & GARDEN
- 📚 History You Never Learned
- 🍳 Everyday Food and Living
- 💻 TECH EXPLAINED
- 👤 Biography Unlimited

## Data Available

- Channel stats (views, subs, video count)
- Per-video stats (views, likes, comments, duration)
- Engagement analysis (like rates)
- Shorts vs long-form comparison
- Upload freshness tracking
- Auto-generated insights
