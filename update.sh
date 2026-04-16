#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# YouTube API key
YT_KEY=$(python3 -c "import json; print(json.load(open('/home/ubuntu/clawd/.secrets/youtube.json'))['api_key'])")
if [ -z "$YT_KEY" ]; then
  echo "ERROR: No YouTube API key found"
  exit 1
fi

echo "[$(date -u)] Fetching YouTube data..."
python3 fetch_data.py "$YT_KEY" > data.json

echo "[$(date -u)] Generating dashboard..."
python3 generate_html.py data.json > index.html

# Check if anything changed
if git diff --quiet index.html 2>/dev/null; then
  echo "[$(date -u)] No changes detected, skipping push."
  exit 0
fi

echo "[$(date -u)] Changes detected, pushing to GitHub..."
git add index.html
git commit -m "Auto-update: $(date -u +'%Y-%m-%d %H:%M UTC')"
git push origin main

echo "[$(date -u)] Done. Dashboard updated."
